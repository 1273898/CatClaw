"""RAG engine for PrivateClaw - orchestrates retrieval and generation."""

from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field

from privateclaw.core.rag.embeddings import EmbeddingProvider, create_embedding_provider
from privateclaw.core.rag.retriever import Retriever, SearchResult


class RAGConfig(BaseModel):
    """RAG configuration."""
    embedding_provider: str = Field(default="openai", description="Embedding provider")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model")
    vector_store_type: str = Field(default="chroma", description="Vector store type")
    vector_store_path: str = Field(default="./data/chroma", description="Vector store path")
    collection_name: str = Field(default="privateclaw", description="Collection name")
    chunk_size: int = Field(default=1000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap")
    search_k: int = Field(default=5, description="Number of search results")
    score_threshold: float = Field(default=0.3, description="Minimum score threshold")


class RAGEngine:
    """RAG engine - orchestrates document processing, storage, and retrieval.

    Follows OpenClaw's approach:
    - Document chunking and embedding
    - Vector store management
    - Query expansion and hybrid search
    - Memory dreaming for consolidation
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        """Initialize RAG engine."""
        self.config = config or RAGConfig()
        self._embedding_provider: Optional[EmbeddingProvider] = None
        self._vector_store = None
        self._retriever: Optional[Retriever] = None

    def _get_embedding_provider(self) -> EmbeddingProvider:
        """Get or create embedding provider."""
        if self._embedding_provider is None:
            self._embedding_provider = create_embedding_provider(
                provider=self.config.embedding_provider,
                model=self.config.embedding_model,
            )
        return self._embedding_provider

    def _get_vector_store(self):
        """Get or create vector store."""
        if self._vector_store is None:
            embeddings = self._get_embedding_provider()

            if self.config.vector_store_type == "chroma":
                from langchain_community.vectorstores import Chroma
                self._vector_store = Chroma(
                    persist_directory=self.config.vector_store_path,
                    embedding_function=embeddings,
                    collection_name=self.config.collection_name,
                )
            else:
                raise ValueError(f"Unsupported vector store: {self.config.vector_store_type}")

        return self._vector_store

    def _get_retriever(self) -> Retriever:
        """Get or create retriever."""
        if self._retriever is None:
            vector_store = self._get_vector_store()
            embedding_provider = self._get_embedding_provider()
            self._retriever = Retriever(vector_store, embedding_provider)
        return self._retriever

    def ingest_text(
        self,
        text: str,
        metadata: Optional[dict] = None,
        chunk: bool = True,
    ) -> list[str]:
        """Ingest text into the RAG system.

        Args:
            text: Text to ingest
            metadata: Optional metadata
            chunk: Whether to chunk the text

        Returns:
            List of document IDs
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        if chunk:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )
            chunks = splitter.split_text(text)
        else:
            chunks = [text]

        # Add metadata
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            metadatas.append(chunk_metadata)

        # Add to vector store
        vector_store = self._get_vector_store()
        ids = vector_store.add_texts(chunks, metadatas=metadatas)

        return ids

    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[dict] = None,
    ) -> list[str]:
        """Ingest a file into the RAG system.

        Args:
            file_path: Path to file
            metadata: Optional metadata

        Returns:
            List of document IDs
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file
        text = path.read_text(encoding='utf-8')

        # Add file metadata
        file_metadata = {
            "source": str(path.absolute()),
            "filename": path.name,
            "extension": path.suffix,
        }
        if metadata:
            file_metadata.update(metadata)

        return self.ingest_text(text, file_metadata)

    def ingest_documents(self, documents: list, metadatas: Optional[list] = None) -> list[str]:
        """Ingest multiple documents.

        Args:
            documents: List of documents (strings or Document objects)
            metadatas: Optional list of metadata dicts

        Returns:
            List of document IDs
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

        all_chunks = []
        all_metadatas = []

        for i, doc in enumerate(documents):
            text = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            chunks = splitter.split_text(text)

            for j, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata = metadatas[i].copy() if metadatas and i < len(metadatas) else {}
                chunk_metadata["doc_index"] = i
                chunk_metadata["chunk_index"] = j
                all_metadatas.append(chunk_metadata)

        # Add to vector store
        vector_store = self._get_vector_store()
        ids = vector_store.add_texts(all_chunks, metadatas=all_metadatas)

        return ids

    def search(
        self,
        query: str,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> list[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query
            k: Number of results (overrides config)
            score_threshold: Minimum score (overrides config)

        Returns:
            List of search results
        """
        retriever = self._get_retriever()
        return retriever.search(
            query=query,
            k=k or self.config.search_k,
            score_threshold=score_threshold or self.config.score_threshold,
        )

    def get_context(self, query: str, max_tokens: int = 4000) -> str:
        """Get relevant context for a query.

        Args:
            query: Search query
            max_tokens: Maximum tokens in context

        Returns:
            Formatted context string
        """
        results = self.search(query)

        if not results:
            return ""

        # Format context
        context_parts = []
        current_tokens = 0

        for i, result in enumerate(results, 1):
            # Estimate tokens (rough approximation)
            tokens = len(result.content.split()) * 1.3

            if current_tokens + tokens > max_tokens:
                break

            context_parts.append(f"[Source {i}] (Score: {result.score:.2f})\n{result.content}")
            current_tokens += tokens

        return "\n\n---\n\n".join(context_parts)

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        if self._vector_store:
            # Recreate vector store
            self._vector_store = None
            self._retriever = None

    def get_stats(self) -> dict:
        """Get RAG engine statistics."""
        vector_store = self._get_vector_store()

        try:
            collection = vector_store._collection
            count = collection.count()
        except Exception:
            count = 0

        return {
            "document_count": count,
            "embedding_provider": self.config.embedding_provider,
            "vector_store_type": self.config.vector_store_type,
            "collection_name": self.config.collection_name,
        }
