"""混合检索模块：BGE-M3语义检索 + BM25关键词检索 + Rerank"""

import json
from typing import Optional

import numpy as np
from langchain_core.tools import tool
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


class HybridRetriever:
    """混合检索器"""

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-m3",
        rerank_model: str = "BAAI/bge-reranker-v2-m3",
        device: str = "cpu",
    ):
        """初始化混合检索器

        Args:
            embedding_model: Embedding模型名称
            rerank_model: Rerank模型名称
            device: 运行设备
        """
        self.device = device
        self._embedding_model = None
        self._rerank_model = None
        self.embedding_model_name = embedding_model
        self.rerank_model_name = rerank_model

        # 文档存储
        self.documents: list[dict] = []
        self.doc_embeddings: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Okapi] = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        """懒加载Embedding模型"""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(
                self.embedding_model_name, device=self.device
            )
        return self._embedding_model

    @property
    def rerank_model(self) -> SentenceTransformer:
        """懒加载Rerank模型"""
        if self._rerank_model is None:
            self._rerank_model = SentenceTransformer(
                self.rerank_model_name, device=self.device
            )
        return self._rerank_model

    def add_documents(self, documents: list[dict]):
        """添加文档到检索库

        Args:
            documents: 文档列表，每个文档包含id, title, text字段
        """
        self.documents = documents

        # 构建BM25索引
        tokenized_docs = [
            f"{doc.get('title', '')} {doc.get('text', '')}".lower().split()
            for doc in documents
        ]
        self.bm25 = BM25Okapi(tokenized_docs)

        # 计算文档向量
        texts = [f"{doc.get('title', '')} {doc.get('text', '')}" for doc in documents]
        self.doc_embeddings = self.embedding_model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )

    def search(
        self,
        query: str,
        max_results: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict]:
        """混合检索

        Args:
            query: 查询文本
            max_results: 最大结果数
            semantic_weight: 语义检索权重
            keyword_weight: 关键词检索权重

        Returns:
            检索结果列表
        """
        if not self.documents:
            return []

        # 语义检索
        query_embedding = self.embedding_model.encode(
            [query], convert_to_numpy=True, show_progress_bar=False
        )[0]

        semantic_scores = np.dot(self.doc_embeddings, query_embedding) / (
            np.linalg.norm(self.doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # 关键词检索
        tokenized_query = query.lower().split()
        keyword_scores = self.bm25.get_scores(tokenized_query)

        # 归一化
        semantic_scores = (semantic_scores - semantic_scores.min()) / (
            semantic_scores.max() - semantic_scores.min() + 1e-8
        )
        keyword_scores = (keyword_scores - keyword_scores.min()) / (
            keyword_scores.max() - keyword_scores.min() + 1e-8
        )

        # 混合评分
        hybrid_scores = semantic_weight * semantic_scores + keyword_weight * keyword_scores

        # 获取Top-K结果
        top_indices = np.argsort(hybrid_scores)[::-1][:max_results]

        results = []
        for idx in top_indices:
            doc = self.documents[idx].copy()
            doc["score"] = float(hybrid_scores[idx])
            doc["semantic_score"] = float(semantic_scores[idx])
            doc["keyword_score"] = float(keyword_scores[idx])
            results.append(doc)

        return results

    def rerank(self, query: str, documents: list[dict], top_k: int = 10) -> list[dict]:
        """使用Reranker对结果精排

        Args:
            query: 查询文本
            documents: 候选文档列表
            top_k: 返回前K个结果

        Returns:
            精排后的文档列表
        """
        if not documents:
            return []

        # 构建查询-文档对
        pairs = [[query, f"{doc.get('title', '')} {doc.get('text', '')}"] for doc in documents]

        # 计算相关性分数
        scores = self.rerank_model.predict(pairs, convert_to_numpy=True)

        # 排序
        sorted_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in sorted_indices:
            doc = documents[idx].copy()
            doc["rerank_score"] = float(scores[idx])
            results.append(doc)

        return results


# 全局检索器实例
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """获取混合检索器单例"""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


@tool
def hybrid_search_advanced(
    query: str,
    documents_json: str,
    max_results: int = 10,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> str:
    """高级混合检索：结合语义检索和关键词检索

    Args:
        query: 搜索查询
        documents_json: 候选文档JSON字符串
        max_results: 最大返回结果数
        semantic_weight: 语义检索权重
        keyword_weight: 关键词检索权重

    Returns:
        检索结果JSON
    """
    try:
        documents = json.loads(documents_json)
        retriever = get_retriever()
        retriever.add_documents(documents)
        results = retriever.search(query, max_results, semantic_weight, keyword_weight)
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)


@tool
def rerank_documents(query: str, documents_json: str, top_k: int = 10) -> str:
    """使用Reranker对文档精排

    Args:
        query: 查询文本
        documents_json: 候选文档JSON字符串
        top_k: 返回前K个结果

    Returns:
        精排结果JSON
    """
    try:
        documents = json.loads(documents_json)
        retriever = get_retriever()
        results = retriever.rerank(query, documents, top_k)
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
