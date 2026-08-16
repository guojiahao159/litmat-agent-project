"""Sciverse API客户端：学术文献实时语义检索与全文定位"""

import json
from typing import Optional

import requests
from langchain_core.tools import tool

from litmat_agent.core.config import settings


class SciverseClient:
    """Sciverse学术搜索API客户端

    提供实时语义检索与全文证据片段定位能力，
    调用记录天然构成可审计的证据链。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """初始化客户端

        Args:
            api_key: API密钥，默认取配置
            base_url: API基础URL，默认取配置
            timeout: 请求超时秒数
        """
        self.api_key = api_key or settings.sciverse_api_key
        self.base_url = (base_url or settings.sciverse_base_url).rstrip("/")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        """是否已配置API密钥"""
        return bool(self.api_key)

    def _headers(self) -> dict:
        """构建请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def search(
        self,
        query: str,
        max_results: int = 10,
        filters: Optional[dict] = None,
    ) -> dict:
        """学术文献搜索（实时语义检索）

        Args:
            query: 检索查询
            max_results: 最大结果数
            filters: 过滤条件（如 year、journal）

        Returns:
            检索结果字典，含 results/total 或 error
        """
        if not self.configured:
            return {"error": "未配置SCIVERSE_API_KEY", "results": []}

        params = {"q": query, "limit": max_results}
        if filters:
            params.update(filters)

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "results": data.get("results", data.get("items", [])),
                "total": data.get("total", data.get("count", 0)),
            }
        except requests.RequestException as e:
            return {"error": f"Sciverse检索失败: {e}", "results": []}

    def get_metadata(self, doi: str) -> dict:
        """按DOI获取文献元数据

        Args:
            doi: 文献DOI

        Returns:
            元数据字典或错误信息
        """
        if not self.configured:
            return {"error": "未配置SCIVERSE_API_KEY"}

        try:
            response = requests.get(
                f"{self.base_url}/metadata",
                params={"doi": doi},
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return {"metadata": response.json()}
        except requests.RequestException as e:
            return {"error": f"元数据获取失败: {e}"}

    def locate_evidence(self, query: str, paper_id: str, top_k: int = 5) -> dict:
        """全文证据片段定位

        在指定文献全文中定位与查询最相关的证据片段，
        返回原文位置信息，用于证据链构建。

        Args:
            query: 查询文本
            paper_id: 文献ID
            top_k: 返回前K个片段

        Returns:
            证据片段列表或错误信息
        """
        if not self.configured:
            return {"error": "未配置SCIVERSE_API_KEY", "evidence": []}

        try:
            response = requests.post(
                f"{self.base_url}/evidence",
                json={"query": query, "paper_id": paper_id, "top_k": top_k},
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "evidence": data.get("evidence", data.get("snippets", [])),
            }
        except requests.RequestException as e:
            return {"error": f"证据定位失败: {e}", "evidence": []}


# 全局客户端单例
_client: Optional[SciverseClient] = None


def get_sciverse_client() -> SciverseClient:
    """获取Sciverse客户端单例"""
    global _client
    if _client is None:
        _client = SciverseClient()
    return _client


@tool
def search_sciverse(query: str, max_results: int = 10) -> str:
    """使用Sciverse API实时检索学术文献

    Args:
        query: 检索查询，如 "sulfide solid electrolyte ionic conductivity"
        max_results: 最大返回结果数

    Returns:
        检索结果JSON字符串
    """
    client = get_sciverse_client()
    result = client.search(query, max_results)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_sciverse_metadata(doi: str) -> str:
    """按DOI获取Sciverse文献元数据

    Args:
        doi: 文献DOI

    Returns:
        元数据JSON字符串
    """
    client = get_sciverse_client()
    result = client.get_metadata(doi)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def locate_evidence_sciverse(query: str, paper_id: str, top_k: int = 5) -> str:
    """在文献全文中定位与查询相关的证据片段

    Args:
        query: 查询文本
        paper_id: 文献ID
        top_k: 返回前K个片段

    Returns:
        证据片段JSON字符串
    """
    client = get_sciverse_client()
    result = client.locate_evidence(query, paper_id, top_k)
    return json.dumps(result, ensure_ascii=False, indent=2)
