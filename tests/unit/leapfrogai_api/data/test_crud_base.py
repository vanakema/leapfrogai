import pytest
from unittest.mock import MagicMock, AsyncMock
from tests.utils.crud_utils import DummyModel, execute_response_format
from tests.mocks.mock_crud_base import mock_crud_base

@pytest.mark.asyncio
async def test_create(mock_crud_base):
    dummy_model_instance = DummyModel(id=1, name="mock-data")
    created_dummy = await mock_crud_base.create(dummy_model_instance)
    assert created_dummy.id == 1
    assert created_dummy.name == "mock-data"

@pytest.mark.asyncio
@pytest.mark.parametrize("filters, mock_response, expected_result", [
    ({"id": 1}, dict(id=1,name="mock-data"), DummyModel(id=1,name="mock-data")),
    ({"id": 1}, [], None),
    ({"id": 1}, {}, None),
    ({"id": 1}, None, None),
    ({}, None, None),
    (None, None, None)
])
async def test_get(mock_crud_base, filters, mock_response, expected_result):
    mock_crud_base.db.table().select().execute.return_value = execute_response_format(mock_response)

    # Run the get method
    result = await mock_crud_base.get(filters)

    # Assert based on expected output
    if expected_result:
        assert result == expected_result
    else:
        assert result is None

@pytest.mark.asyncio
async def test_list(mock_crud_base):
    dummy_list = await mock_crud_base.list({})
    assert len(dummy_list) == 1
    assert dummy_list[0].id == 1
    assert dummy_list[0].name == "mock-data"

@pytest.mark.asyncio
async def test_update(mock_crud_base):
    dummy_model_instance = DummyModel(id=1, name="updated-data")
    mock_crud_base.db.table().update().execute.return_value = execute_response_format(dummy_model_instance.model_dump())
    updated_dummy = await mock_crud_base.update("1", dummy_model_instance)
    assert updated_dummy == dummy_model_instance

@pytest.mark.asyncio
async def test_delete(mock_crud_base):
    result = await mock_crud_base.delete({"id": 1})
    assert result is True