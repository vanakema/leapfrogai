import pytest
from unittest.mock import MagicMock, AsyncMock
from src.leapfrogai_api.data.crud_base import CRUDBase
from pydantic import BaseModel


class DummyModel(BaseModel):
    id: int
    name: str


@pytest.fixture
def crud_base_instance():
    # Create an AsyncMock for the db client
    db = AsyncMock()
    
    mock_insert = AsyncMock()  # Use AsyncMock here to allow await on insert().execute()
    mock_insert.execute.return_value=((None, [{"id": 1, "name": "mock-data"}]), None)
    
    mock_table = MagicMock()
    mock_table.insert.return_value = mock_insert
    db.table = MagicMock(return_value=mock_table)
    
    return CRUDBase(db=db, model=DummyModel, table_name="dummy_table")


@pytest.mark.asyncio
async def test_create(crud_base_instance):
    dummy_model_instance = DummyModel(id=1, name="mock-data")
    created_dummy = await crud_base_instance.create(dummy_model_instance)
    assert created_dummy.id == 1
    assert created_dummy.name == "mock-data"
