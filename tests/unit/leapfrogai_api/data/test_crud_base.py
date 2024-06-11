import pytest
from unittest.mock import MagicMock, AsyncMock
from src.leapfrogai_api.data.crud_base import CRUDBase
from pydantic import BaseModel

class DummyModel(BaseModel):
    id: int
    name: str

@pytest.fixture
def mock_crud_base():
    # Create an AsyncMock for the db client
    db = AsyncMock()

    mock_table = MagicMock()
    db.table = MagicMock(return_value=mock_table)

    mock_insert = AsyncMock()
    mock_insert.execute.return_value = ((None, [{"id": 1, "name": "mock-data"}]), None)
    mock_table.insert.return_value = mock_insert

    mock_select = AsyncMock()
    mock_select.execute.return_value = ((None, [{"id": 1, "name": "mock-data"}]), None)
    mock_select.eq = MagicMock(return_value = mock_select)
    mock_table.select.return_value = mock_select

    mock_update = AsyncMock()
    mock_update.execute.return_value = ((None, [{"id": 1, "name": "updated-data"}]), None)
    mock_update.eq = MagicMock(return_value = mock_update)
    mock_table.update.return_value = mock_update

    mock_delete = AsyncMock()
    mock_delete.execute.return_value = ((None, True), None)
    mock_delete.eq = MagicMock(return_value = mock_delete)
    mock_table.delete.return_value = mock_delete

    return CRUDBase(db=db, model=DummyModel, table_name="dummy_table")

@pytest.mark.asyncio
async def test_create(mock_crud_base):
    dummy_model_instance = DummyModel(id=1, name="mock-data")
    created_dummy = await mock_crud_base.create(dummy_model_instance)
    assert created_dummy.id == 1
    assert created_dummy.name == "mock-data"

@pytest.mark.asyncio
async def test_get(mock_crud_base):
    dummy = await mock_crud_base.get({"id": 1})
    assert dummy.id == 1
    assert dummy.name == "mock-data"

@pytest.mark.asyncio
async def test_list(mock_crud_base):
    dummy_list = await mock_crud_base.list({})
    assert len(dummy_list) == 1
    assert dummy_list[0].id == 1
    assert dummy_list[0].name == "mock-data"

@pytest.mark.asyncio
async def test_update(mock_crud_base):
    dummy_model_instance = DummyModel(id=1, name="updated-data")
    updated_dummy = await mock_crud_base.update("1", dummy_model_instance)
    assert updated_dummy.id == 1
    assert updated_dummy.name == "updated-data"

@pytest.mark.asyncio
async def test_delete(mock_crud_base):
    result = await mock_crud_base.delete({"id": 1})
    assert result is True