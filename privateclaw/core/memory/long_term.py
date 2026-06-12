"""Long-term memory (vector store) for PrivateClaw."""

from typing import Optional
from datetime import datetime


class LongTermMemory:
    """Long-term memory using vector store for semantic search."""

    def __init__(
        self,
        vector_store_type: str = "chroma",
        vector_store_path: str = "./data/chroma",
        embedding_model: str = "text-embedding-3-small",
    ):
        """Initialize long-term memory."""
        self.vector_store_type = vector_store_type
        self.vector_store_path = vector_store_path
        self.embedding_model = embedding_model
        self._vector_store = None
        self._embeddings = None

    def _get_embeddings(self):
        """Get embeddings model."""
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings
            self._embeddings = OpenAIEmbeddings(model=self.embedding_model)
        return self._embeddings

    def _get_vector_store(self):
        """Get or create vector store."""
        if self._vector_store is None:
            embeddings = self._get_embeddings()

            if self.vector_store_type == "chroma":
                from langchain_community.vectorstores import Chroma
                self._vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=embeddings,
                    collection_name="privateclaw_memory",
                )
            else:
                raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")

        return self._vector_store

    async def store(self, content: str, metadata: Optional[dict] = None) -> None:
        """Store content in vector store."""
        vector_store = self._get_vector_store()

        if metadata is None:
            metadata = {}
        metadata["stored_at"] = datetime.now().isoformat()

        vector_store.add_texts(
            texts=[content],
            metadatas=[metadata],
        )

    async def search(self, query: str, k: int = 5) -> list[dict]:
        """Search for similar content."""
        vector_store = self._get_vector_store()

        results = vector_store.similarity_search_with_score(query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
            }
            for doc, score in results
        ]

    async def delete(self, ids: list[str]) -> None:
        """Delete entries by ID."""
        vector_store = self._get_vector_store()
        vector_store.delete(ids)

    async def clear(self) -> None:
        """Clear all entries."""
        # Recreate vector store
        self._vector_store = None
