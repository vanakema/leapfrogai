"""OpenAI completions router."""

from typing import Annotated, AsyncGenerator, Any
from fastapi import HTTPException, APIRouter, Depends
from fastapi.security import HTTPBearer
from leapfrogai_api.backend.grpc_client import (
    completion,
    stream_completion,
    stream_chat_completion_raw,
)
from leapfrogai_api.backend.types import (
    CompletionRequest,
    ChatCompletionResponse,
    ChatCompletionRequest,
)
from leapfrogai_api.routers.supabase_session import Session
from leapfrogai_api.utils import get_model_config
from leapfrogai_api.utils.config import Config
import leapfrogai_sdk as lfai

router = APIRouter(prefix="/openai/v1/completions", tags=["openai/completions"])
security = HTTPBearer()


@router.post("")
async def complete(
    session: Session,
    req: CompletionRequest,
    model_config: Annotated[Config, Depends(get_model_config)],
):
    """Complete a prompt with the given model."""
    # Get the model backend configuration
    model = model_config.get_model_backend(req.model)
    if model is None:
        raise HTTPException(
            status_code=405,
            detail=f"Model {req.model} not found. Currently supported models are {list(model_config.models.keys())}",
        )

    request = lfai.CompletionRequest(
        prompt=req.prompt,  # type: ignore
        max_new_tokens=req.max_tokens,
        temperature=req.temperature,
    )

    if req.stream:
        return await stream_completion(model, request)
    else:
        return await completion(model, request)


async def complete_stream_raw(
    session: Session,
    req: ChatCompletionRequest,
    model_config: Annotated[Config, Depends(get_model_config)],
) -> AsyncGenerator[ChatCompletionResponse, Any]:
    """Complete a prompt with the given model."""
    # Get the model backend configuration
    model = model_config.get_model_backend(req.model)
    if model is None:
        raise HTTPException(
            status_code=405,
            detail=f"Model {req.model} not found. Currently supported models are {list(model_config.models.keys())}",
        )

    request = lfai.ChatCompletionRequest(
        prompt=req.prompt,  # type: ignore
        max_new_tokens=req.max_tokens,
        temperature=req.temperature,
    )

    return stream_chat_completion_raw(model, request)
