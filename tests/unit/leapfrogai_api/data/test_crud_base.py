import pytest
from unittest.mock import AsyncMock
from src.leapfrogai_api.data.crud_base import CRUDBase
from pydantic import BaseModel

class DummyModel(BaseModel):
    id: int
    name: str

@pytest.fixture
def crud_base_instance():
    db = AsyncMock()
    mock_table = AsyncMock()
    db.table.return_value = mock_table
    
    mock_insert = AsyncMock()
    mock_select = AsyncMock()
    mock_update = AsyncMock()
    mock_delete = AsyncMock()
    
    mock_table.insert.return_value = mock_insert
    mock_table.select.return_value = mock_select
    mock_table.update.return_value = mock_update
    mock_table.delete.return_value = mock_delete
    
    mock_insert.execute.return_value = AsyncMock(return_value=([{"id": 1, "name": "Dummy"}], None))
    mock_select.execute.return_value = AsyncMock(return_value=([{"id": 1, "name": "Dummy"}], None))
    mock_update.execute.return_value = AsyncMock(return_value=([{"id": 1, "name": "Updated Dummy"}], None))
    mock_delete.execute.return_value = AsyncMock(return_value=(None, None))
    
    return CRUDBase(db=db, model=DummyModel, table_name="dummy_table")

@pytest.mark.asyncio
async def test_create(crud_base_instance):
    dummy_model_instance = DummyModel(id=1, name="Dummy")
    created_dummy = await crud_base_instance.create(dummy_model_instance)
    assert created_dummy.id == 1
    assert created_dummy.name == "Dummy"

@pytest.mark.asyncio
async def test_get(crud_base_instance):
    dummy_data = {"id": 1, "name": "Dummy"}
    created_dummy = await crud_base_instance.create(dummy_data)
    retrieved_dummy = await crud_base_instance.get(created_dummy.id)
    assert retrieved_dummy.id == created_dummy.id
    assert retrieved_dummy.name == created_dummy.name

@pytest.mark.asyncio
async def test_list(crud_base_instance):
    dummy_data = {"id": 1, "name": "Dummy"}
    await crud_base_instance.create(dummy_data)
    dummy_list = await crud_base_instance.list()
    assert len(dummy_list) == 1
    assert dummy_list[0].id == dummy_data["id"]
    assert dummy_list[0].name == dummy_data["name"]

@pytest.mark.asyncio
async def test_update(crud_base_instance):
    dummy_data = {"id": 1, "name": "Dummy"}
    created_dummy = await crud_base_instance.create(dummy_data)
    updated_dummy_data = {"name": "Updated Dummy"}
    updated_dummy = await crud_base_instance.update(created_dummy.id, updated_dummy_data)
    assert updated_dummy.id == created_dummy.id
    assert updated_dummy.name == updated_dummy_data["name"]

@pytest.mark.asyncio
async def test_delete(crud_base_instance):
    dummy_data = {"id": 1, "name": "Dummy"}
    created_dummy = await crud_base_instance.create(dummy_data)
    await crud_base_instance.delete(created_dummy.id)
    deleted_dummy = await crud_base_instance.get(created_dummy.id)
    assert deleted_dummy is None
