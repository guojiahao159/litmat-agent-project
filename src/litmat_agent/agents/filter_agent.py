"""文献筛选Agent：相关性评估与去重"""

import json
import re
from typing import Optional

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings


@tool
def assess_relevance(paper_metadata: str, query: str) -> str:
    """评估文献与研究问题的相关性

    基于标题/摘要关键词覆盖率与位置加权打分（0-1）。

    Args:
        paper_metadata: 文献元数据JSON字符串（含title/abstract字段）
        query: 研究问题

    Returns:
        相关性评分JSON
    """
    try:
        paper = json.loads(paper_metadata)
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        query_words = [
            w.lower()
            for w in re.findall(r"[A-Za-z]+", query)
            if len(w) > 2
        ]
        if not query_words:
            return json.dumps(
                {"relevance_score": 0.5, "matched_keywords": []},
                ensure_ascii=False,
            )

        title_lower = title.lower()
        abstract_lower = abstract.lower()

        matched = []
        title_score = 0.0
        abstract_score = 0.0

        for word in set(query_words):
            if word in title_lower:
                title_score += 1.0
                matched.append(word)
            elif word in abstract_lower:
                abstract_score += 1.0
                matched.append(word)

        # 标题匹配权重3倍于摘要匹配
        score = (title_score * 3 + abstract_score) / (len(query_words) * 3)
        score = min(1.0, round(score, 3))

        return json.dumps(
            {
                "relevance_score": score,
                "matched_keywords": matched,
                "title": title,
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def deduplicate_papers(papers_json: str) -> str:
    """文献去重：按DOI（优先）或标题规范化后去重

    Args:
        papers_json: 文献列表JSON字符串

    Returns:
        去重后的文献列表JSON
    """
    try:
        papers = json.loads(papers_json)
        seen_doi = set()
        seen_title = set()
        unique = []
        duplicates = 0

        for paper in papers:
            # 先规范化标题（无论是否有DOI都登记，避免跨DOI/无DOI重复漏检）
            title_key = re.sub(
                r"[^a-z0-9]+", "",
                (paper.get("title") or "").lower(),
            )

            doi = (paper.get("doi") or "").lower().strip()
            if doi:
                if doi in seen_doi:
                    duplicates += 1
                    continue
                seen_doi.add(doi)
                if title_key:
                    seen_title.add(title_key)
                unique.append(paper)
                continue

            # 无DOI时按标题规范化去重
            if title_key and title_key in seen_title:
                duplicates += 1
                continue
            if title_key:
                seen_title.add(title_key)
            unique.append(paper)

        return json.dumps(
            {
                "papers": unique,
                "removed_duplicates": duplicates,
                "original_count": len(papers),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def filter_by_threshold(papers_json: str, query: str, threshold: float = 0.3) -> str:
    """按相关性阈值筛选文献

    Args:
        papers_json: 文献列表JSON字符串
        query: 研究问题
        threshold: 相关性阈值（0-1），低于该值的文献被过滤

    Returns:
        筛选后的文献列表JSON
    """
    try:
        papers = json.loads(papers_json)
        kept = []
        for paper in papers:
            result = json.loads(
                assess_relevance.invoke(
                    {"paper_metadata": json.dumps(paper, ensure_ascii=False), "query": query}
                )
            )
            score = result.get("relevance_score", 0.0)
            if score >= threshold:
                paper["relevance_score"] = score
                kept.append(paper)

        return json.dumps(
            {
                "papers": kept,
                "filtered_out": len(papers) - len(kept),
                "threshold": threshold,
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def create_filter_agent(model: Optional[str] = None):
    """创建文献筛选Agent

    专注相关性评估与去重，作为文献检索Agent的下游组件

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，文献筛选Agent将以演示模式创建")
        class MockAgent:
            def invoke(self, inputs):
                return {
                    "messages": [
                        type("Message", (), {
                            "content": "演示模式：请配置API密钥后使用完整功能"
                        })()
                    ]
                }
        return MockAgent()

    agent = create_deep_agent(
        model=model,
        tools=[assess_relevance, deduplicate_papers, filter_by_threshold],
        system_prompt="""你是LitMat-Agent的文献筛选模块，负责从候选文献集中筛选高相关文献。

你可以使用以下工具：
1. assess_relevance: 评估单篇文献与研究问题的相关性（0-1评分）
2. deduplicate_papers: 按DOI/标题去重
3. filter_by_threshold: 按相关性阈值批量筛选

筛选原则：
- 优先保留直接研究目标材料的文献
- 综述性文献适当降权（避免重复计数）
- 保留矛盾结论的文献（供后续Gap识别）
- 默认阈值0.3，材料化学核心文献可放宽至0.2""",
    )

    return agent


# 便捷函数
def get_default_filter_agent():
    """获取默认配置的文献筛选Agent"""
    return create_filter_agent()
