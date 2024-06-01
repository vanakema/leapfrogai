"""Test the API endpoints for assistants."""

import os

import pytest
from fastapi import Response, status
from fastapi.testclient import TestClient
from openai.types.beta import Thread, ThreadDeleted
from leapfrogai_api.backend.types import CreateThreadRequest, ModifyThreadRequest
from leapfrogai_api.routers.openai.threads import router as threads_router
from leapfrogai_api.routers.openai.files import router as files_router


class MissingEnvironmentVariable(Exception):
    pass


headers: dict[str, str] = {}

try:
    headers = {"Authorization": f"Bearer {os.environ['SUPABASE_USER_JWT']}"}
except KeyError as exc:
    raise MissingEnvironmentVariable(
        "SUPABASE_USER_JWT must be defined for the test to pass. "
        "Please check the api README for instructions on obtaining this token."
    ) from exc

threads_client = TestClient(threads_router, headers=headers)
files_client = TestClient(files_router, headers=headers)

thread_response: Response


# Create a threads with the previously created file and fake embeddings
@pytest.fixture(scope="session", autouse=True)
def create_thread():
    """Create a thread for testing. Requires a running Supabase instance."""

    global thread_response  # pylint: disable=global-statement

    request = CreateThreadRequest(
        messages=None,
        tool_resources=None,
        metadata={},
    )

    thread_response = threads_client.post(
        "/openai/v1/threads", json=request.model_dump()
    )


def test_create():
    """Test creating a thread. Requires a running Supabase instance."""
    assert thread_response.status_code == status.HTTP_200_OK
    assert Thread.model_validate(
        thread_response.json()
    ), "Create should create a Thread."


def test_get():
    """Test getting a threads. Requires a running Supabase instance."""
    threads_id = thread_response.json()["id"]
    get_response = threads_client.get(
        f"/openai/v1/threads/{threads_id}"
    )
    assert get_response.status_code == status.HTTP_200_OK
    assert Thread.model_validate(
        get_response.json()
    ), f"Get should return Thread {threads_id}."


def test_modify():
    """Test modifying a thread. Requires a running Supabase instance."""
    thread_id = thread_response.json()["id"]
    request = ModifyThreadRequest(
        tool_resources=None,
        metadata={"test": "modified"},
    )

    modify_response = threads_client.post(
        f"/openai/v1/threads/{thread_id}",
        json=request.model_dump(),
    )
    assert modify_response.status_code == status.HTTP_200_OK
    assert Thread.model_validate(
        modify_response.json()
    ), "Should return a Thread."
    assert modify_response.json()["metadata"]["test"] == "modified", "Should be modified."


def test_get_modified():
    """Test getting a modified threads. Requires a running Supabase instance."""
    threads_id = thread_response.json()["id"]
    get_modified_response = threads_client.get(
        f"/openai/v1/threads/{threads_id}"
    )
    assert get_modified_response.status_code == status.HTTP_200_OK
    assert Thread.model_validate(
        get_modified_response.json()
    ), f"Get should return modified Thread {threads_id}."
    assert get_modified_response.json()["metadata"]["test"] == "modified", "Should be modified."


def test_delete():
    """Test deleting a thread. Requires a running Supabase instance."""
    thread_id = thread_response.json()["id"]
    delete_response = threads_client.delete(
        f"/openai/v1/threads/{thread_id}"
    )
    assert delete_response.status_code == status.HTTP_200_OK
    assert ThreadDeleted.model_validate(
        delete_response.json()
    ), "Should return a ThreadDeleted object."
    assert delete_response.json()["deleted"] is True, "Should be able to delete."


def test_delete_twice():
    """Test deleting a thread twice. Requires a running Supabase instance."""
    thread_id = thread_response.json()["id"]
    delete_response = threads_client.delete(
        f"/openai/v1/threads/{thread_id}"
    )
    assert delete_response.status_code == status.HTTP_200_OK
    assert ThreadDeleted.model_validate(
        delete_response.json()
    ), "Should return a ThreadDeleted object."
    assert (
            delete_response.json()["deleted"] is False
    ), "Should not be able to delete twice."


def test_get_nonexistent():
    """Test getting a nonexistent thread. Requires a running Supabase instance."""
    thread_id = thread_response.json()["id"]
    get_response = threads_client.get(
        f"/openai/v1/threads/{thread_id}"
    )
    assert get_response.status_code == status.HTTP_200_OK
    assert (
            get_response.json() is None
    ), f"Get should not return deleted Thread {thread_id}."
