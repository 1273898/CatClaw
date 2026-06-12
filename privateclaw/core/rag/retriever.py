"""Retriever for PrivateClaw RAG system."""

from typing import Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Search result model."""
    content: str = Field(description="Document content")
    metadata: dict = Field(default_factory=dict, description="Document metadata")
    score: float = Field(default=0.0, description="Relevance score")


class Retriever:
    """Document retriever for RAG system.

    Implements OpenClaw-style retrieval with:
    - Query expansion
    - Hybrid search (vector + keyword)
    - Result reranking
    - Deduplication
    """

    def __init__(self, vector_store, embedding_provider):
        """Initialize retriever."""
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def expand_query(self, query: str) -> list[str]:
        """Expand query into multiple search queries.

        This follows OpenClaw's query expansion approach:
        - Extract keywords
        - Remove stop words
        - Generate variations
        """
        # Simple keyword extraction
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
            'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'and', 'but', 'or', 'if', 'while', 'about', 'against', 'up', 'down',
        }

        # Extract keywords
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Generate queries
        queries = [query]  # Original query

        # Add keyword-only query
        if keywords:
            queries.append(' '.join(keywords))

        return queries

    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0,
        expand_query: bool = True,
    ) -> list[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum score threshold
            expand_query: Whether to expand query

        Returns:
            List of search results
        """
        queries = self.expand_query(query) if expand_query else [query]

        all_results = []
        seen_contents = set()

        for q in queries:
            # Vector search
            results = self.vector_store.similarity_search_with_score(q, k=k)

            for doc, score in results:
                # Deduplicate
                content_hash = hash(doc.page_content)
                if content_hash in seen_contents:
                    continue
                seen_contents.add(content_hash)

                # Apply score threshold
                if score < score_threshold:
                    continue

                all_results.append(SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=score,
                ))

        # Sort by score (higher is better)
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Return top k results
        return all_results[:k]

    async def asearch(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0,
        expand_query: bool = True,
    ) -> list[SearchResult]:
        """Async search for relevant documents."""
        # For now, use sync implementation
        return self.search(query, k, score_threshold, expand_query)

    def add_documents(self, documents: list, metadatas: Optional[list] = None) -> None:
        """Add documents to the vector store."""
        texts = [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in documents]
        self.vector_store.add_texts(texts, metadatas=metadatas)

    def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        self.vector_store.delete(ids)
