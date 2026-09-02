"""
向量存储与检索（可选，用于财报文档 RAG 知识库问答）
支持 ChromaDB（本地）/ FAISS
"""
from typing import List, Optional
from app.utils.logger import logger


class VectorStore:
    def __init__(self, persist_dir: str = "./ai/knowledge_base/chroma_db"):
        self.persist_dir = persist_dir
        self.collection = None
        self.embedding_model = None
        self._initialized = False

    def initialize(self):
        """初始化向量数据库和嵌入模型"""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            client = chromadb.Client(
                ChromaSettings(
                    persist_directory=self.persist_dir,
                    anonymized_telemetry=False,
                )
            )

            self.collection = client.get_or_create_collection(
                name="stock_knowledge",
                metadata={"description": "个股金融知识库"},
            )

            self._initialized = True
            logger.info("向量数据库初始化成功")
        except ImportError:
            logger.warning("chromadb 未安装，向量检索功能不可用")
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")

    def add_documents(self, documents: List[str], metadatas: List[dict] = None):
        """添加文档到向量库"""
        if not self._initialized:
            logger.warning("向量数据库未初始化，跳过文档添加")
            return

        if not documents:
            return

        try:
            ids = [f"doc_{i}_{hash(doc) % 100000}" for i, doc in enumerate(documents)]
            self.collection.add(
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids,
            )
            logger.info(f"已添加 {len(documents)} 条文档到向量库")
        except Exception as e:
            logger.error(f"添加文档到向量库失败: {e}")

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """向量相似度检索"""
        if not self._initialized:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            return [
                {
                    "content": doc,
                    "metadata": meta,
                    "distance": dist,
                }
                for doc, meta, dist in zip(
                    results.get("documents", [[]])[0],
                    results.get("metadatas", [[]])[0],
                    results.get("distances", [[]])[0],
                )
            ]
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    def clear(self):
        """清空向量库"""
        if self._initialized and self.collection:
            try:
                self.collection.delete(where={})
                logger.info("向量库已清空")
            except Exception as e:
                logger.error(f"清空向量库失败: {e}")


vector_store = VectorStore()