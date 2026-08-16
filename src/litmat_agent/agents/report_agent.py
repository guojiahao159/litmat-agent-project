"""报告生成Agent：结构化调研报告生成"""

import json
from datetime import datetime
from typing import Optional

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings


REPORT_TEMPLATE = """# 文献调研报告

## 一、研究问题
{query}

## 二、调研概况
- 检索文献数：{retrieved_count}
- 筛选相关文献数：{filtered_count}
- 抽取材料实体数：{material_count}
- 抽取性能数据数：{property_count}

## 三、关键材料
{materials}

## 四、研究空白（Research Gaps）
{gaps}

## 五、候选假设
{hypotheses}

## 六、证据链
{evidence}

## 七、结论与建议
{conclusions}

---
报告生成时间：{timestamp}
"""


@tool
def generate_report_structure(
    query: str,
    retrieved_count: int = 0,
    filtered_count: int = 0,
    material_count: int = 0,
    property_count: int = 0,
    materials: str = "",
    gaps: str = "",
    hypotheses: str = "",
    evidence: str = "",
    conclusions: str = "",
) -> str:
    """生成结构化调研报告

    按模板填充调研数据，生成Markdown格式报告。

    Args:
        query: 研究问题
        retrieved_count: 检索文献数
        filtered_count: 筛选相关文献数
        material_count: 抽取材料实体数
        property_count: 抽取性能数据数
        materials: 关键材料描述
        gaps: 研究空白描述
        hypotheses: 候选假设描述
        evidence: 证据链描述
        conclusions: 结论与建议

    Returns:
        Markdown格式报告
    """
    try:
        materials_text = materials or "（暂无）"
        gaps_text = gaps or "（暂无）"
        hypotheses_text = hypotheses or "（暂无）"
        evidence_text = evidence or "（暂无）"
        conclusions_text = conclusions or "（暂无）"

        report = REPORT_TEMPLATE.format(
            query=query,
            retrieved_count=retrieved_count,
            filtered_count=filtered_count,
            material_count=material_count,
            property_count=property_count,
            materials=materials_text,
            gaps=gaps_text,
            hypotheses=hypotheses_text,
            evidence=evidence_text,
            conclusions=conclusions_text,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        return report
    except Exception as e:
        return f"报告生成失败: {e}"


@tool
def format_references(references_json: str, style: str = "numbered") -> str:
    """格式化参考文献列表

    Args:
        references_json: 参考文献列表JSON字符串（含title/authors/year/journal/doi字段）
        style: 引用风格（numbered数字编号/apa风格）

    Returns:
        格式化后的参考文献文本
    """
    try:
        refs = json.loads(references_json)
        lines = []

        for i, ref in enumerate(refs, 1):
            authors = ref.get("authors", [])
            if isinstance(authors, list):
                author_text = ", ".join(authors[:3])
                if len(authors) > 3:
                    author_text += " et al."
            else:
                author_text = str(authors)

            title = ref.get("title", "")
            journal = ref.get("journal", "")
            year = ref.get("year", "")
            doi = ref.get("doi", "")

            if style == "numbered":
                line = f"[{i}] {author_text}. {title}. {journal}. {year}."
            else:  # apa
                line = f"{author_text} ({year}). {title}. {journal}."

            if doi:
                line += f" DOI: {doi}"
            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        return f"参考文献格式化失败: {e}"


@tool
def summarize_findings(analysis_json: str) -> str:
    """汇总分析结果生成结论摘要

    Args:
        analysis_json: 分析结果JSON字符串（含research_gaps/hypotheses字段）

    Returns:
        结论摘要文本
    """
    try:
        analysis = json.loads(analysis_json)
        gaps = analysis.get("research_gaps", [])
        hypotheses = analysis.get("hypotheses", [])

        parts = []

        if gaps:
            parts.append(f"发现{len(gaps)}个研究空白：")
            for i, gap in enumerate(gaps, 1):
                parts.append(
                    f"  {i}. {gap.get('description', gap.get('gap_type', ''))}"
                )

        if hypotheses:
            parts.append(f"生成{len(hypotheses)}条候选假设：")
            for i, hyp in enumerate(hypotheses, 1):
                parts.append(f"  {i}. {hyp.get('note', hyp.get('type', ''))}")

        if not parts:
            return "未发现显著研究空白或候选假设。"

        return "\n".join(parts)
    except Exception as e:
        return f"结论汇总失败: {e}"


def create_report_agent(model: Optional[str] = None):
    """创建报告生成Agent

    基于调研结果生成结构化Markdown报告

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，报告生成Agent将以演示模式创建")
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
        tools=[generate_report_structure, format_references, summarize_findings],
        system_prompt="""你是LitMat-Agent的报告生成模块，负责生成结构化调研报告。

你可以使用以下工具：
1. generate_report_structure: 按模板生成Markdown格式报告
2. format_references: 格式化参考文献列表（支持numbered/apa风格）
3. summarize_findings: 汇总分析结果生成结论摘要

报告规范：
- 使用Markdown格式，章节结构清晰
- 每个研究空白必须附证据链引用
- 区分"文献事实"与"待验证假设"
- 参考文献格式统一，DOI完整
- 结论必须可追溯到具体文献""",
    )

    return agent


# 便捷函数
def get_default_report_agent():
    """获取默认配置的报告生成Agent"""
    return create_report_agent()
