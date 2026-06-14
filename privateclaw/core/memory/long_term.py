"""Long-term memory (vector store) for CatClaw."""

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
        self._use_local_embeddings = True  # 使用本地 embedding 避免 API 超时

    def _get_embeddings(self):
        """Get embeddings model."""
        if self._embeddings is None:
            try:
                # 尝试使用本地 embedding 模型
                if self._use_local_embeddings:
                    # 优先使用新的 langchain-huggingface 包
                    try:
                        from langchain_huggingface import HuggingFaceEmbeddings
                    except ImportError:
                        # 降级到旧版
                        from langchain_community.embeddings import HuggingFaceEmbeddings

                    self._embeddings = HuggingFaceEmbeddings(
                        model_name="all-MiniLM-L6-v2",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                else:
                    from langchain_openai import OpenAIEmbeddings
                    self._embeddings = OpenAIEmbeddings(model=self.embedding_model)
            except Exception as e:
                print(f"[Memory] Embedding 初始化失败: {e}")
                # Fallback: 使用简单的向量化
                from langchain_community.embeddings import FakeEmbeddings
                self._embeddings = FakeEmbeddings(size=384)
        return self._embeddings

    def _get_vector_store(self):
        """Get or create vector store."""
        if self._vector_store is None:
            embeddings = self._get_embeddings()

            if self.vector_store_type == "chroma":
                try:
                    from langchain_chroma import Chroma
                except ImportError:
                    from langchain_community.vectorstores import Chroma

                self._vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=embeddings,
                    collection_name="catclaw_memory",
                )
            else:
                raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")

        return self._vector_store

    async def store(self, content: str, metadata: Optional[dict] = None) -> None:
        """Store content in vector store."""
        try:
            vector_store = self._get_vector_store()

            if metadata is None:
                metadata = {}
            metadata["stored_at"] = datetime.now().isoformat()

            vector_store.add_texts(
                texts=[content],
                metadatas=[metadata],
            )
        except Exception as e:
            print(f"[Memory] 存储失败: {e}")

    async def search(self, query: str, k: int = 5) -> list[dict]:
        """Search for similar content."""
        try:
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
        except Exception as e:
            print(f"[Memory] 搜索失败: {e}")
            return []

    async def delete(self, ids: list[str]) -> None:
        """Delete entries by ID."""
        try:
            vector_store = self._get_vector_store()
            vector_store.delete(ids)
        except Exception as e:
            print(f"[Memory] 删除失败: {e}")

    async def clear(self) -> None:
        """Clear all entries."""
        # Recreate vector store
        self._vector_store = None
