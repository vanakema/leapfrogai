"""OpenAI Compliant Threads API Router."""

import logging
import traceback
import uuid
from typing import Iterable, Union, AsyncGenerator, Any
from uuid import UUID

from fastapi import HTTPException, APIRouter, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from openai.types.beta import Thread, ThreadDeleted, Assistant
from openai.types.beta.thread_create_and_run_params import (
    ThreadMessage,
)
from openai.types.beta.threads import Message, MessageDeleted, Run, Text
from openai.types.beta.threads.message_content import MessageContent
from openai.types.beta.threads.text_delta_block import TextDeltaBlock
from openai.types.beta.threads.text_delta import TextDelta
from openai.types.beta.threads.message_delta import MessageDelta
from openai.types.beta.assistant_stream_event import (
    AssistantStreamEvent,
    MessageDeltaEvent,
    ThreadMessageDelta,
)
from openai.types.beta.threads.message_content_part_param import MessageContentPartParam
from openai.types.beta.threads.runs import RunStep
from openai.types.beta.threads.text_content_block import TextContentBlock
from postgrest.base_request_builder import SingleAPIResponse
from pydantic_core import ValidationError

from leapfrogai_api.backend.rag.query import QueryService
from leapfrogai_api.backend.types import (
    CreateThreadRequest,
    ModifyThreadRequest,
    CreateMessageRequest,
    ModifyMessageRequest,
    RunCreateParamsRequest,
    ThreadRunCreateParamsRequest,
    RunCreateParams,
    ModifyRunRequest,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    RAGResponse,
)
from leapfrogai_api.backend.validators import (
    AssistantToolChoiceParamValidator,
    TextContentBlockParamValidator,
)
from leapfrogai_api.data.crud_message import CRUDMessage
from leapfrogai_api.data.crud_run import CRUDRun
from leapfrogai_api.data.crud_thread import CRUDThread
from leapfrogai_api.routers.openai.assistants import retrieve_assistant
from leapfrogai_api.routers.openai.chat import chat_complete
from leapfrogai_api.routers.openai.completions import complete_stream_raw
from leapfrogai_api.routers.supabase_session import Session
from leapfrogai_api.utils import get_model_config

router = APIRouter(prefix="/openai/v1/threads", tags=["openai/threads"])
security = HTTPBearer()


@router.post("")
async def create_thread(request: CreateThreadRequest, session: Session) -> Thread:
    """Create a thread."""
    new_messages: list[Message] = []
    new_thread: Thread | None = None
    try:
        crud_thread = CRUDThread(db=session)

        thread = Thread(
            id="",  # Leave blank to have Postgres generate a UUID
            created_at=0,  # Leave blank to have Postgres generate a timestamp
            metadata=request.metadata,
            object="thread",
            tool_resources=request.tool_resources,
        )

        new_thread = await crud_thread.create(object_=thread)

        if new_thread and request.messages:
            """Once the thread has been created, add all of the request's messages to the DB"""
            for message in request.messages:
                new_messages.append(
                    await create_message(
                        new_thread.id,
                        CreateMessageRequest(
                            role=message.role,
                            content=message.content,
                            attachments=message.attachments,
                            metadata=message.metadata,
                        ),
                        session,
                    )
                )

        return new_thread
    except Exception as exc:
        if new_thread:
            for message in new_messages:
                """Clean up any messages added prior to the error"""
                await delete_message(
                    thread_id=new_thread.id, message_id=message.id, session=session
                )

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create thread",
        ) from exc


def can_use_rag(request: ThreadRunCreateParamsRequest | RunCreateParamsRequest) -> bool:
    has_tool_choice: bool = request.tool_choice is not None
    has_tool_resources: bool = True

    if isinstance(request, ThreadRunCreateParamsRequest):
        """'Create thread and run' requires 'tool_resources' while 'Create run' does not"""
        has_tool_resources = bool(
            request.tool_resources
            and request.tool_resources.file_search
            and request.tool_resources.file_search.vector_store_ids
        )

    if has_tool_choice and has_tool_resources:
        if isinstance(request.tool_choice, str):
            return request.tool_choice == "auto" or request.tool_choice == "required"
        else:
            try:
                if AssistantToolChoiceParamValidator.validate_python(
                    request.tool_choice
                ):
                    return request.tool_choice.get("type") == "file_search"
            except ValidationError:
                traceback.print_exc()
                logging.error(
                    "Cannot use RAG for request, failed to validate tool for thread"
                )
                return False

    return False


async def generate_message_for_thread(
    session: Session,
    request: ThreadRunCreateParamsRequest | RunCreateParamsRequest,
    thread_id: str,
) -> Union[Message, AsyncGenerator[ThreadMessageDelta, Any]]:
    # Get existing messages
    thread_messages: list[Message] = await list_messages(thread_id, session)
    # Convert messages to ChatMessages
    chat_messages: list[ChatMessage] = [
        ChatMessage(role=message.role, content=message.content[0].text.value)
        for message in thread_messages
    ]

    use_rag: bool = can_use_rag(request)

    if use_rag:
        query_service = QueryService(db=session)

        for vector_store_id in request.tool_resources.file_search.vector_store_ids:
            rag_results_raw: SingleAPIResponse[
                RAGResponse
            ] = await query_service.query_rag(
                query=chat_messages[0].content,
                vector_store_id=vector_store_id,
            )
            rag_responses: RAGResponse = RAGResponse(data=rag_results_raw.data)

            for count, rag_response in enumerate(rag_responses.data):
                """Insert the RAG response messages just before the user's query"""
                response_with_instructions: str = (
                    f"<start attached file {count}'s content>\n"
                    f"{rag_response.content}"
                    f"\n<end attached file {count}'s content>"
                )
                chat_messages.insert(
                    1, ChatMessage(role="user", content=response_with_instructions)
                )

    if request.stream:
        chat_response: AsyncGenerator[
            ChatCompletionResponse, Any
        ] = await complete_stream_raw(
            req=ChatCompletionRequest(
                model=str(request.model),
                messages=chat_messages,
                functions=None,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=request.stream,
                stop=None,
                max_tokens=request.max_completion_tokens,
            ),
            model_config=get_model_config(),
            session=session,
        )
        async for streaming_response in chat_response:
            random_uuid: UUID = uuid.uuid4()
            thread_message_event: ThreadMessageDelta = ThreadMessageDelta(
                data=MessageDeltaEvent(
                    id=str(random_uuid),
                    delta=MessageDelta(
                        content=TextDeltaBlock(
                            index=128281482814,
                            type="text",
                            text=TextDelta(
                                annotations=[],
                                value=streaming_response.choices[0].message.content,
                            ),
                        ),
                        role="assistant",
                    ),
                    object="thread.message.delta",
                ),
                event="thread.message.delta",
            )
            yield thread_message_event
    else:
        # Generate a new message and add it to the thread creation request
        chat_response: ChatCompletionResponse | StreamingResponse = await chat_complete(
            req=ChatCompletionRequest(
                model=str(request.model),
                messages=chat_messages,
                functions=None,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=request.stream,
                stop=None,
                max_tokens=request.max_completion_tokens,
            ),
            model_config=get_model_config(),
            session=session,
        )

        message_content: TextContentBlock = TextContentBlock(
            text=Text(annotations=[], value=chat_response.choices[0].message.content),
            type="text",
        )

        new_message = Message(
            id="",
            created_at=0,
            object="thread.message",
            status="in_progress",
            thread_id="",
            content=[message_content],
            role="assistant",
        )

        # Add the generated response to the db
        return await create_message(
            thread_id,
            CreateMessageRequest(
                role=new_message.role,
                content=new_message.content,
                attachments=new_message.attachments,
                metadata=new_message.metadata,
            ),
            session,
        )


async def update_request_with_assistant_data(
    session: Session, request: ThreadRunCreateParamsRequest | RunCreateParamsRequest
) -> ThreadRunCreateParamsRequest | RunCreateParamsRequest:
    assistant: Assistant | None = await retrieve_assistant(
        session=session, assistant_id=request.assistant_id
    )

    model: str | None = request.model if request.model else assistant.model
    temperature: float | None = (
        request.temperature if request.temperature else assistant.temperature
    )
    top_p: float | None = request.top_p if request.top_p else assistant.top_p

    # Create a copy of the request with proper values for model, temperature, and top_p
    return request.model_copy(
        update={"model": model, "temperature": temperature, "top_p": top_p}
    )


def convert_content_param_to_content(
    thread_message_content: Union[str, Iterable[MessageContentPartParam]],
) -> MessageContent:
    """Converts messages from MessageContentPartParam to MessageContent"""
    if isinstance(thread_message_content, str):
        return TextContentBlock(
            text=Text(annotations=[], value=thread_message_content),
            type="text",
        )
    else:
        result: str = ""

        for message_content_part in thread_message_content:
            try:
                if TextContentBlockParamValidator.validate_python(message_content_part):
                    result += message_content_part.get("text")
            except ValidationError:
                traceback.print_exc()
                logging.error(f"Failed to validate message content part")
                continue

        return TextContentBlock(
            text=Text(annotations=[], value=result),
            type="text",
        )


@router.post("/{thread_id}/runs", response_model=None)
async def create_run(
    thread_id: str, session: Session, request: RunCreateParamsRequest
) -> Union[Run, StreamingResponse]:
    """Create a run."""

    try:
        run_request: (
            ThreadRunCreateParamsRequest | RunCreateParamsRequest
        ) = await update_request_with_assistant_data(session, request)

        if request.additional_messages:
            """If additional messages exist, create them in the DB as a part of this thread"""
            for additional_message in request.additional_messages:
                # Convert the messages content into the correct format
                message_content: MessageContent = convert_content_param_to_content(
                    additional_message.get("content")
                )

                await create_message(
                    thread_id,
                    CreateMessageRequest(
                        role=additional_message.get("role"),
                        content=[message_content],
                        attachments=additional_message.get("attachments"),
                        metadata=additional_message.get("metadata"),
                    ),
                    session,
                )

        # Generate a new response based on the existing thread
        message_or_stream: (
            Message | AsyncGenerator[ThreadMessageDelta, Any]
        ) = await generate_message_for_thread(session, run_request, thread_id)

        if request.stream:
            async for message in message_or_stream:
                yield message
        else:
            crud_run = CRUDRun(db=session)

            create_params: RunCreateParams = RunCreateParams(**run_request.__dict__)

            run = Run(
                id="",  # Leave blank to have Postgres generate a UUID
                created_at=0,  # Leave blank to have Postgres generate a timestamp
                thread_id=thread_id,
                object="thread.run",
                status="completed",
                **create_params.__dict__,
            )
            return await crud_run.create(object_=run)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create run",
        ) from exc


@router.post("/runs", response_model=None)
async def create_thread_and_run(
    session: Session, request: ThreadRunCreateParamsRequest
) -> Union[Run, StreamingResponse]:
    """Create a thread and run."""

    try:
        thread_request: CreateThreadRequest = CreateThreadRequest(
            messages=[],
            tool_resources=request.tool_resources,
            metadata=request.metadata,
        )

        if request.thread:
            """If the thread exists, convert all of its messages into a form that can be used by create_thread."""
            thread_messages: Iterable[ThreadMessage] = request.thread.get("messages")
            for message in thread_messages:
                try:
                    # Convert the messages content into the correct format
                    message_content: MessageContent = convert_content_param_to_content(
                        message.get("content")
                    )

                    thread_request.messages.append(
                        Message(
                            id="",
                            created_at=0,
                            object="thread.message",
                            status="in_progress",
                            thread_id="",
                            content=[message_content],
                            role=message.get("role"),
                            attachments=message.get("attachments"),
                            metadata=message.get("metadata"),
                        )
                    )
                except ValueError as exc:
                    logging.error(f"\t{exc}")
                    continue

        run_request: (
            ThreadRunCreateParamsRequest | RunCreateParamsRequest
        ) = await update_request_with_assistant_data(session, request)

        new_thread: Thread = await create_thread(
            thread_request,
            session,
        )

        message_or_stream = await generate_message_for_thread(
            session, run_request, new_thread.id
        )

        if request.stream:
            pass
        else:
            crud_run = CRUDRun(db=session)

            create_params: RunCreateParams = RunCreateParams(**run_request.__dict__)

            run = Run(
                id="",  # Leave blank to have Postgres generate a UUID
                created_at=0,  # Leave blank to have Postgres generate a timestamp
                thread_id=new_thread.id,
                object="thread.run",
                status="completed",  # This is always completed as the new message is already created by this point
                parallel_tool_calls=False,
                **create_params.__dict__,
            )

            return await crud_run.create(object_=run)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create run",
        ) from exc


@router.get("/{thread_id}/runs")
async def list_runs(thread_id: str, session: Session) -> list[Run]:
    """List all the runs in a thread."""
    try:
        crud_run = CRUDRun(db=session)
        runs = await crud_run.list(filters={"thread_id": thread_id})

        return runs
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list runs for thread {thread_id}",
        ) from exc


@router.get("/{thread_id}/runs/{run_id}")
async def retrieve_run(thread_id: str, run_id: str, session: Session) -> Run:
    """Retrieve a run."""
    crud_run = CRUDRun(db=session)
    return await crud_run.get(filters={"id": run_id, "thread_id": thread_id})


@router.post("/{thread_id}/runs/{run_id}")
async def modify_run(
    thread_id: str, run_id: str, request: ModifyRunRequest, session: Session
) -> Run:
    """Modify a run."""
    run = CRUDRun(db=session)

    if not (old_run := await run.get(filters={"id": run_id, "thread_id": thread_id})):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    try:
        new_run = Run(
            id=run_id,
            thread_id=thread_id,
            created_at=old_run.created_at,
            metadata=getattr(request, "metadata", old_run.metadata),
            object="thread.run",
        )

        return await run.update(
            id_=run_id,
            object_=new_run,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse run request",
        ) from exc


@router.post("/{thread_id}/runs/{run_id}/submit_tool_outputs")
async def submit_tool_outputs(thread_id: str, run_id: str, session: Session) -> Run:
    """Submit tool outputs for a run."""
    # TODO: Implement this function
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{thread_id}/runs/{run_id}/cancel")
async def cancel_run(thread_id: str, run_id: str, session: Session) -> Run:
    """Cancel a run."""
    # TODO: Implement this function
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{thread_id}/runs/{run_id}/steps")
async def list_run_steps(
    thread_id: str, run_id: str, session: Session
) -> list[RunStep]:
    """List all the steps in a run."""
    # TODO: Implement this function
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{thread_id}/runs/{run_id}/steps/{step_id}")
async def retrieve_run_step(
    thread_id: str, run_id: str, step_id: str, session: Session
) -> RunStep:
    """Retrieve a step."""
    # TODO: Implement this function
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{thread_id}")
async def retrieve_thread(thread_id: str, session: Session) -> Thread | None:
    """Retrieve a thread."""
    crud_thread = CRUDThread(db=session)
    return await crud_thread.get(filters={"id": thread_id})


@router.post("/{thread_id}")
async def modify_thread(
    thread_id: str, request: ModifyThreadRequest, session: Session
) -> Thread:
    """Modify a thread."""
    thread = CRUDThread(db=session)

    if not (old_thread := await thread.get(filters={"id": thread_id})):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    try:
        new_thread = Thread(
            id=thread_id,
            created_at=old_thread.created_at,
            metadata=getattr(request, "metadata", old_thread.metadata),
            object="thread",
            tool_resources=getattr(
                request, "tool_resources", old_thread.tool_resources
            ),
        )

        return await thread.update(
            id_=thread_id,
            object_=new_thread,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse thread request",
        ) from exc


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str, session: Session) -> ThreadDeleted:
    """Delete a thread."""
    try:
        crud_thread = CRUDThread(db=session)

        thread_deleted = await crud_thread.delete(filters={"id": thread_id})
        return ThreadDeleted(
            id=thread_id,
            object="thread.deleted",
            deleted=bool(thread_deleted),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to delete thread",
        ) from exc


@router.post("/{thread_id}/messages")
async def create_message(
    thread_id: str, request: CreateMessageRequest, session: Session
) -> Message:
    """Create a message."""
    try:
        crud_message = CRUDMessage(db=session)

        message = Message(
            id="",  # Leave blank to have Postgres generate a UUID
            attachments=request.attachments,
            content=request.content,
            created_at=0,  # Leave blank to have Postgres generate a timestamp
            metadata=request.metadata,
            object="thread.message",
            role=request.role,
            status="completed",
            thread_id=thread_id,
        )
        return await crud_message.create(object_=message)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create message",
        ) from exc


@router.get("/{thread_id}/messages")
async def list_messages(thread_id: str, session: Session) -> list[Message]:
    """List all the messages in a thread."""
    try:
        crud_message = CRUDMessage(db=session)
        messages = await crud_message.list(filters={"thread_id": thread_id})

        return messages
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list messages",
        ) from exc


@router.get("/{thread_id}/messages/{message_id}")
async def retrieve_message(
    thread_id: str, message_id: str, session: Session
) -> Message | None:
    """Retrieve a message."""
    crud_message = CRUDMessage(db=session)
    return await crud_message.get(filters={"id": message_id, "thread_id": thread_id})


@router.post("/{thread_id}/messages/{message_id}")
async def modify_message(
    thread_id: str, message_id: str, request: ModifyMessageRequest, session: Session
) -> Message:
    """Modify a message."""
    message = CRUDMessage(db=session)

    if not (
        old_message := await message.get(
            filters={"id": message_id, "thread_id": thread_id}
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    try:
        new_message = Message(
            id=message_id,
            created_at=old_message.created_at,
            content=old_message.content,
            metadata=getattr(request, "metadata", old_message.metadata),
            object="thread.message",
            attachments=old_message.attachments,
            role=old_message.role,
            status=old_message.status,
            thread_id=thread_id,
        )

        return await message.update(
            id_=message_id,
            object_=new_message,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse message request",
        ) from exc


@router.delete("/{thread_id}/messages/{message_id}")
async def delete_message(
    thread_id: str, message_id: str, session: Session
) -> MessageDeleted:
    """Delete message from a thread."""

    crud_message = CRUDMessage(db=session)
    message_deleted = await crud_message.delete(
        filters={"id": message_id, "thread_id": thread_id}
    )
    return MessageDeleted(
        id=message_id,
        deleted=bool(message_deleted),
        object="thread.message.deleted",
    )
