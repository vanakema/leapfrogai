"""Indexing service for RAG files."""

import tempfile

from fastapi import HTTPException, UploadFile, status
from langchain_core.embeddings import Embeddings
from openai.types.beta.vector_stores import VectorStoreFile
from openai.types.beta.vector_stores.vector_store_file import LastError
from supabase_py_async import AsyncClient
from leapfrogai_api.backend.rag.document_loader import load_file, split
from leapfrogai_api.backend.rag.leapfrogai_embeddings import LeapfrogAIEmbeddings
from leapfrogai_api.data.async_supabase_vector_store import AsyncSupabaseVectorStore
from leapfrogai_api.data.crud_file_bucket import CRUDFileBucket
from leapfrogai_api.data.crud_file_object import CRUDFileObject, FilterFileObject
from leapfrogai_api.data.crud_vector_store_file import CRUDVectorStoreFile
from leapfrogai_api.backend.types import VectorStoreFileStatus

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
