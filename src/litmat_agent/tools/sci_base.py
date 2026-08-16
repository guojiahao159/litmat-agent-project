"""Sci-Base本地文献检索模块"""

import json
from pathlib import Path
from typing import Optional

from elasticsearch import Elasticsearch
from langchain_core.tools import tool

from litmat_agent.core.config import settings


class SciBaseClient:
    """Sci-Base本地文献库客户端"""

    def __init__(self, es_host: str = "localhost", es_port: int = 9200):
        """初始化Elasticsearch连接

        Args:
            es_host: ES主机地址
            es_port: ES端口
        """
        self.es = Elasticsearch([{"host": es_host, "port": es_port, "scheme": "http"}])
        self.index_name = "sci_base_literature"
        self._ensure_index()

    def _ensure_index(self):
        """确保索引存在"""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "analyzer": "standard"},
                        "abstract": {"type": "text", "analyzer": "standard"},
                        "full_text": {"type": "text", "analyzer": "standard"},
                        "authors": {"type": "keyword"},
                        "year": {"type": "integer"},
                        "journal": {"type": "keyword"},
                        "doi": {"type": "keyword"},
                        "materials": {"type": "keyword"},
                        "properties": {"type": "keyword"},
                        "embedding": {"type": "dense_vector", "dims": 1024},
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)

    def index_paper(self, paper_data: dict) -> bool:
        """索引单篇文献

        Args:
            paper_data: 文献数据字典

        Returns:
            是否成功
        """
        try:
            self.es.index(index=self.index_name, document=paper_data)
            return True
        except Exception as e:
            print(f"索引文献失败: {e}")
            return False

    def search(
        self,
        query: str,
        max_results: int = 10,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """关键词检索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            filters: 过滤条件

        Returns:
            文献列表
        """
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "abstract^2", "full_text"],
                            }
                        }
                    ]
                }
            },
            "size": max_results,
        }

        if filters:
            search_body["query"]["bool"]["filter"] = [
                {"term": {k: v}} for k, v in filters.items()
            ]

        try:
            response = self.es.search(index=self.index_name, body=search_body)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"检索失败: {e}")
            return []

    def vector_search(
        self,
        query_vector: list[float],
        max_results: int = 10,
    ) -> list[dict]:
        """向量检索

        Args:
            query_vector: 查询向量
            max_results: 最大结果数

        Returns:
            文献列表
        """
        search_body = {
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": max_results,
                "num_candidates": 100,
            }
        }

        try:
            response = self.es.search(index=self.index_name, body=search_body)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"向量检索失败: {e}")
            return []


# 全局客户端实例
_sci_base_client: Optional[SciBaseClient] = None


def get_sci_base_client() -> SciBaseClient:
    """获取Sci-Base客户端单例"""
    global _sci_base_client
    if _sci_base_client is None:
        _sci_base_client = SciBaseClient()
    return _sci_base_client


@tool
def search_sci_base(query: str, max_results: int = 10) -> str:
    """搜索Sci-Base本地文献库

    Args:
        query: 搜索查询，如 "sulfide solid electrolyte"
        max_results: 返回结果数量

    Returns:
        文献列表JSON字符串
    """
    try:
        client = get_sci_base_client()
        results = client.search(query, max_results)
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)


@tool
def index_literature(paper_data: str) -> str:
    """将文献数据索引到Sci-Base

    Args:
        paper_data: 文献数据JSON字符串

    Returns:
        操作结果
    """
    try:
        data = json.loads(paper_data)
        client = get_sci_base_client()
        success = client.index_paper(data)
        return json.dumps({"success": success}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
