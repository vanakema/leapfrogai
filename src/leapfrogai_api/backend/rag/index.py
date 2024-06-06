"""Indexing service for RAG files."""

import tempfile
import time
import traceback


from fastapi import HTTPException, UploadFile, status
from langchain_core.embeddings import Embeddings
from openai.types.beta.vector_store import FileCounts
from openai.types.beta.vector_stores import VectorStore, VectorStoreFile
from openai.types.beta.vector_stores.vector_store_file import LastError
from supabase_py_async import AsyncClient
from leapfrogai_api.backend.rag.document_loader import load_file, split
from leapfrogai_api.backend.rag.leapfrogai_embeddings import LeapfrogAIEmbeddings
from leapfrogai_api.data.async_supabase_vector_store import AsyncSupabaseVectorStore
from leapfrogai_api.data.crud_file_bucket import CRUDFileBucket
from leapfrogai_api.data.crud_file_object import CRUDFileObject, FilterFileObject
from leapfrogai_api.data.crud_vector_store import CRUDVectorStore
from leapfrogai_api.data.crud_vector_store_file import CRUDVectorStoreFile
from leapfrogai_api.backend.types import (
    VectorStoreStatus,
    VectorStoreFileStatus,
    CreateVectorStoreRequest,
)

# Allows for overwriting type of embeddings that will be instantiated
embeddings_type: type[Embeddings] | type[LeapfrogAIEmbeddings] | None = (
    LeapfrogAIEmbeddings
)


class IndexingService:
    """Service for indexing files into a vector store."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.embeddings = embeddings_type()

    async def index_file(self, vector_store_id: str, file_id: str) -> VectorStoreFile:
        """Index a file into a vector store."""
        crud_vector_store_file = CRUDVectorStoreFile(db=self.db)

        if await crud_vector_store_file.get(
            filters={"vector_store_id": vector_store_id, "id": file_id}
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File already indexed"
            )

        crud_file_object = CRUDFileObject(db=self.db)
        crud_file_bucket = CRUDFileBucket(db=self.db, model=UploadFile)

        file_object = await crud_file_object.get(filters=FilterFileObject(id=file_id))

        if not file_object:
            raise ValueError("File not found")
        file_bytes = await crud_file_bucket.download(id_=file_id)

        with tempfile.NamedTemporaryFile(suffix=file_object.filename) as temp_file:
            temp_file.write(file_bytes)
            temp_file.seek(0)
            documents = await load_file(temp_file.name)
            chunks = await split(documents)

            if len(chunks) == 0:
                vector_store_file = VectorStoreFile(
                    id=file_id,
                    created_at=0,
                    last_error=LastError(
                        message="No text found in file", code="parsing_error"
                    ),
                    object="vector_store.file",
                    status=VectorStoreFileStatus.FAILED.value,
                    vector_store_id=vector_store_id,
                )
                return await crud_vector_store_file.create(object_=vector_store_file)

            vector_store_file = VectorStoreFile(
                id=file_id,
                created_at=0,
                last_error=None,
                object="vector_store.file",
                status=VectorStoreFileStatus.IN_PROGRESS.value,
                vector_store_id=vector_store_id,
            )

            vector_store_file = await crud_vector_store_file.create(
                object_=vector_store_file
            )

            try:
                vector_store_client = AsyncSupabaseVectorStore(
                    db=self.db, embedding=self.embeddings
                )

                ids = await vector_store_client.aadd_documents(
                    documents=chunks,
                    vector_store_id=vector_store_id,
                    file_id=file_id,
                )

                if len(ids) == 0:
                    vector_store_file.status = VectorStoreFileStatus.FAILED.value
                else:
                    vector_store_file.status = VectorStoreFileStatus.COMPLETED.value

                await crud_vector_store_file.update(
                    id_=vector_store_file.id, object_=vector_store_file
                )
            except Exception as e:
                vector_store_file.status = VectorStoreFileStatus.FAILED.value
                await crud_vector_store_file.update(
                    id_=vector_store_file.id, object_=vector_store_file
                )
                raise e

            return await crud_vector_store_file.get(
                filters={"vector_store_id": vector_store_id, "id": file_id}
            )

    async def create_vector_store(
        self, request: CreateVectorStoreRequest
    ) -> VectorStore:
        """Create a new vector store given a set of file ids"""
        crud_vector_store = CRUDVectorStore(db=self.db)

        last_active_at = int(time.time())

        expires_after, expires_at = request.get_expiry(last_active_at)

        vector_store = VectorStore(
            id="",  # Leave blank to have Postgres generate a UUID
            bytes=0,  # Automatically calculated by DB
            created_at=0,  # Leave blank to have Postgres generate a timestamp
            file_counts=FileCounts(
                cancelled=0, completed=0, failed=0, in_progress=0, total=0
            ),
            last_active_at=last_active_at,  # Set to current time
            metadata=request.metadata,
            name=request.name,
            object="vector_store",
            status=VectorStoreStatus.IN_PROGRESS.value,
            expires_after=expires_after,
            expires_at=expires_at,
        )
        try:
            new_vector_store = await crud_vector_store.create(object_=vector_store)
            if request.file_ids != []:
                for file_id in request.file_ids:
                    response = await self.index_file(
                        vector_store_id=new_vector_store.id, file_id=file_id
                    )

                    if response.status == VectorStoreFileStatus.COMPLETED.value:
                        new_vector_store.file_counts.completed += 1
                    elif response.status == VectorStoreFileStatus.FAILED.value:
                        new_vector_store.file_counts.failed += 1
                    elif response.status == VectorStoreFileStatus.IN_PROGRESS.value:
                        new_vector_store.file_counts.in_progress += 1
                    elif response.status == VectorStoreFileStatus.CANCELLED.value:
                        new_vector_store.file_counts.cancelled += 1
                    new_vector_store.file_counts.total += 1

            new_vector_store.status = VectorStoreStatus.COMPLETED.value

            return await crud_vector_store.update(
                id_=new_vector_store.id,
                object_=new_vector_store,
            )
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create vector store",
            ) from exc
