"""RAG (Retrieval-Augmented Generation) module for PrivateClaw."""

from privateclaw.core.rag.engine import RAGEngine
from privateclaw.core.rag.embeddings import EmbeddingProvider, create_embedding_provider
from privateclaw.core.rag.retriever import Retriever
from privateclaw.core.rag.dreaming import MemoryDreaming

__all__ = [
    "RAGEngine",
    "EmbeddingProvider",
    "create_embedding_provider",
    "Retriever",
    "MemoryDreaming",
]
