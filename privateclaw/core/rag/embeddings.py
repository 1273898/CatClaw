"""Embedding providers for PrivateClaw RAG system."""

from typing import Optional, Protocol
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        """Initialize OpenAI embedding provider."""
        self.model = model
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            from langchain_openai import OpenAIEmbeddings
            kwargs = {"model": self.model}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._client = OpenAIEmbeddings(**kwargs)
        return self._client

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        client = self._get_client()
        return client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        client = self._get_client()
        return client.embed_query(text)

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        # text-embedding-3-small: 1536 dimensions
        # text-embedding-3-large: 3072 dimensions
        if "large" in self.model:
            return 3072
        return 1536


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize local embedding provider."""
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Get or create model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        model = self._get_model()
        embedding = model.encode([text], show_progress_bar=False)
        return embedding[0].tolist()

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider for local models."""

    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        """Initialize Ollama embedding provider."""
        self.model = model
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """Get or create Ollama client."""
        if self._client is None:
            try:
                from langchain_community.embeddings import OllamaEmbeddings
                self._client = OllamaEmbeddings(
                    model=self.model,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "langchain-community is required for Ollama embeddings. "
                    "Install with: pip install langchain-community"
                )
        return self._client

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        client = self._get_client()
        return client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        client = self._get_client()
        return client.embed_query(text)

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        # nomic-embed-text: 768 dimensions
        return 768


def create_embedding_provider(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> EmbeddingProvider:
    """Create an embedding provider.

    Args:
        provider: Provider name (openai, local, ollama)
        model: Model name (provider-specific)
        api_key: API key (for OpenAI)
        **kwargs: Additional provider-specific arguments

    Returns:
        EmbeddingProvider instance
    """
    if provider == "openai":
        return OpenAIEmbeddingProvider(
            model=model or "text-embedding-3-small",
            api_key=api_key,
        )
    elif provider == "local":
        return LocalEmbeddingProvider(
            model_name=model or "all-MiniLM-L6-v2",
        )
    elif provider == "ollama":
        return OllamaEmbeddingProvider(
            model=model or "nomic-embed-text",
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
