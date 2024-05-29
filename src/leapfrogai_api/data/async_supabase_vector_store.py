"""This module contains the AsyncSupabaseVectorStore class."""

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from supabase_py_async import AsyncClient

from leapfrogai_api.backend.rag.leapfrogai_embeddings import LeapfrogAIEmbeddings


# Partially implements the Langchain Core VectorStore interface
class AsyncSupabaseVectorStore:
    """An async vector store that uses Supabase as the backend.

    Args:
        client (AsyncClient): The Supabase async client.
        embedding (Embeddings): The embedding model.

    """

    def __init__(
        self,
        db: AsyncClient,
        embedding: Embeddings | LeapfrogAIEmbeddings | None = None,
    ) -> None:
        """Initializes the AsyncSupabaseVectorStore."""
        self.client: AsyncClient = db
        self.embedding: Embeddings = embedding
        # The name of the database table. Defaults to "vector_content".
        self.table_name: str = "vector_content"
        # The name of the query to execute. Defaults to "match_vectors".
        self.query_name: str = "match_vectors"

    async def adelete_file(self, vector_store_id: str, file_id: str) -> bool:
        """Delete a file from the vector store.

        Args:
            vector_store_id (str): The ID of the vector store.
            file_id (str): The ID of the file to be deleted.

        Returns:
            dict: The response from the database after deleting the file.

        """
        data, _count = (
            await self.client.from_(self.table_name)
            .delete()
            .eq("vector_store_id", vector_store_id)
            .eq("file_id", file_id)
            .execute()
        )

        _, response = data

        return bool(response)

    async def aadd_documents(
        self,
        documents: list[Document],
        vector_store_id: str,
        file_id: str,
    ) -> list[str]:
        """Adds documents to the vector store.

        Args:
            documents (list[Document]): A list of Langchain Document objects to be added.
            vector_store_id (str): The ID of the vector store where the documents will be added.
            file_id (str): The ID of the file associated with the documents.

        Returns:
            List[str]: A list of IDs assigned to the added documents.

        Raises:
            Any exceptions that may occur during the execution of the method.

        """
        ids = []  # Initialize the ids list
        embeddings = await self.embedding.aembed_documents(
            texts=[document.page_content for document in documents]
        )

        for document, embedding in zip(documents, embeddings):
            response = await self._aadd_vector(
                vector_store_id=vector_store_id,
                file_id=file_id,
                content=document.page_content,
                metadata=document.metadata,
                embedding=embedding,
            )
            ids.append(response.data[0]["id"])

        return ids

    async def asimilarity_search(self, query: str, vector_store_id: str, k: int = 4):
        """Searches for similar documents.

        Args:
            query (str): The query string.
            vector_store_id (str): The ID of the vector store to search in.
            k (int, optional): The number of similar documents to retrieve. Defaults to 4.

        Returns:
            The response from the database after executing the similarity search.

        """
        vector = await self.embedding.aembed_query(query)

        user_id: str = (await self.client.auth.get_user()).user.id

        params = {
            "query_embedding": vector,
            "match_limit": k,
            "vs_id": vector_store_id,
            "user_id": user_id,
        }

        query_builder = self.client.rpc(self.query_name, params=params)

        response = await query_builder.execute()

        return response

    async def _adelete_vector(
        self,
        vector_store_id: str,
        file_id: str,
    ) -> dict:
        """Delete a vector from the vector store.

        Args:
            vector_store_id (str): The ID of the vector store.
            file_id (str): The ID of the file associated with the vector.

        Returns:
            dict: The response from the database after deleting the vector.

        """
        response = (
            await self.client.from_(self.table_name)
            .delete()
            .eq("vector_store_id", vector_store_id)
            .eq("file_id", file_id)
            .execute()
        )
        return response

    async def _aadd_vector(
        self,
        vector_store_id: str,
        file_id: str,
        content: str,
        metadata: str,
        embedding: list[float],
    ) -> dict:
        """Add a vector to the vector store.

        Args:
            vector_store_id (str): The ID of the vector store.
            file_id (str): The ID of the file associated with the vector.
            content (str): The content of the vector.
            metadata (str): The metadata associated with the vector.
            embedding (list[float]): The embedding of the vector.

        Returns:
            dict: The response from the database after inserting the vector.

        """

        user_id: str = (await self.client.auth.get_user()).user.id

        row: dict[str, any] = {
            "user_id": user_id,
            "vector_store_id": vector_store_id,
            "file_id": file_id,
            "content": content,
            "metadata": metadata,
            "embedding": embedding,
        }
        response = await self.client.from_(self.table_name).insert(row).execute()
        return response
