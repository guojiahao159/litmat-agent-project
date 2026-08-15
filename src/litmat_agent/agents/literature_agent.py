"""文献调研Agent：基于DeepAgent实现"""

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings
from litmat_agent.tools import search_literature, extract_material_info, hybrid_search


# 定义文献调研专用工具
@tool
def summarize_paper(paper_text: str) -> str:
    """总结文献核心内容

    Args:
        paper_text: 文献全文或摘要

    Returns:
        文献总结
    """
    return "文献总结（待实现）"


@tool
def identify_research_gap(papers_summary: str) -> str:
    """识别研究空白

    Args:
        papers_summary: 多篇文献的总结

    Returns:
        Research Gap分析
    """
    return "Research Gap识别（待实现）"


def create_literature_agent(model: str = None):
    """创建文献调研Agent

    Args:
        model: 使用的LLM模型，默认使用配置中的default_model

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    agent = create_deep_agent(
        model=model,
        tools=[
            search_literature,
            extract_material_info,
            hybrid_search,
            summarize_paper,
            identify_research_gap,
        ],
        system_prompt="""你是LitMat-Agent，一个专业的材料科学文献调研助手。

你的任务是帮助用户调研固态电解质领域的科学文献，具体包括：
1. 根据用户的研究问题，检索相关文献
2. 从文献中抽取材料成分、结构、性能等关键信息
3. 分析多篇文献，识别研究空白和矛盾结论
4. 生成结构化的调研报告

请始终基于文献事实回答，区分文献事实、跨文献推论和待验证假设。
如果不确定，请明确说明，不要编造信息。""",
    )

    return agent


# 便捷函数
def get_default_agent():
    """获取默认配置的文献调研Agent"""
    return create_literature_agent()
