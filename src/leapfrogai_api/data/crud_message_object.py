"""CRUD Operations for Message."""

from pydantic import Field
from openai.types.beta.threads import Message
from supabase_py_async import AsyncClient
from leapfrogai_api.data.crud_base import CRUDBase


class AuthMessageObject(Message):
    """A wrapper for the message that includes a user_id for auth"""

    user_id: str = Field(default="")


class CRUDMessageObject(CRUDBase[AuthMessageObject]):
    """CRUD Operations for message"""

    def __init__(self, db: AsyncClient):
        super().__init__(db=db, model=AuthMessageObject, table_name="message_objects")

    async def create(self, object_: Message) -> AuthMessageObject | None:
        """Create new message."""
        user_id: str = (await self.db.auth.get_user()).user.id
        return await super().create(
            object_=AuthMessageObject(user_id=user_id, **object_.model_dump())
        )

    async def get(self, id_: str) -> AuthMessageObject | None:
        """Get a vector store by its ID."""

        return await super().get(id_=id_)

    async def list(self) -> list[AuthMessageObject] | None:
        """List all messages."""

        return await super().list()

    async def update(self, id_: str, object_: Message) -> AuthMessageObject | None:
        """Update a message by its ID."""

        dict_ = object_.model_dump()

        data, _count = (
            await self.db.table(self.table_name).update(dict_).eq("id", id_).execute()
        )

        _, response = data

        if response:
            return self.model(**response[0])
        return None

    async def delete(self, id_: str) -> bool:
        """Delete a message by its ID."""
        return await super().delete(id_=id_)
