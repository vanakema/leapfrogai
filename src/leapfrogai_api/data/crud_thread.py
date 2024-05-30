"""CRUD Operations for Thread."""

from pydantic import Field
from openai.types.beta import Thread
from supabase_py_async import AsyncClient
from leapfrogai_api.data.crud_base import CRUDBase


class AuthThread(Thread):
    """A wrapper for the thread that includes a user_id for auth"""

    user_id: str = Field(default="")


class CRUDThread(CRUDBase[AuthThread]):
    """CRUD Operations for thread"""

    def __init__(self, db: AsyncClient):
        super().__init__(db=db, model=AuthThread, table_name="thread_objects")

    async def create(self, object_: Thread) -> AuthThread | None:
        """Create new thread."""
        user_id: str = (await self.db.auth.get_user()).user.id
        return await super().create(
            object_=AuthThread(user_id=user_id, **object_.model_dump())
        )

    async def get(self, id_: str) -> AuthThread | None:
        """Get a vector store by its ID."""

        return await super().get(id_=id_)

    async def list(self) -> list[AuthThread] | None:
        """List all threads."""

        return await super().list()

    async def update(self, id_: str, object_: Thread) -> AuthThread | None:
        """Update a thread by its ID."""

        dict_ = object_.model_dump()

        data, _count = (
            await self.db.table(self.table_name).update(dict_).eq("id", id_).execute()
        )

        _, response = data

        if response:
            return self.model(**response[0])
        return None

    async def delete(self, id_: str) -> bool:
        """Delete a thread by its ID."""
        return await super().delete(id_=id_)
