"""任务规划Agent：研究问题分解与调研计划生成

作为多Agent系统的入口组件，将用户研究问题分解为
可执行的子任务并生成结构化调研计划。
"""

import json
import re
from typing import Optional

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings

# 领域关键词 → 重点关注属性（中英双语）
DOMAIN_PROPERTIES = {
    "electrolyte": ["ionic_conductivity", "activation_energy", "electrochemical_stability_window"],
    "电解质": ["ionic_conductivity", "activation_energy", "electrochemical_stability_window"],
    "solid": ["ionic_conductivity", "thermal_stability", "mechanical_property"],
    "固态": ["ionic_conductivity", "thermal_stability", "mechanical_property"],
    "sulfide": ["ionic_conductivity", "air_stability", "interfacial_stability"],
    "硫化物": ["ionic_conductivity", "air_stability", "interfacial_stability"],
    "polymer": ["ionic_conductivity", "mechanical_property", "thermal_stability"],
    "聚合物": ["ionic_conductivity", "mechanical_property", "thermal_stability"],
    "oxide": ["ionic_conductivity", "thermal_stability"],
    "氧化物": ["ionic_conductivity", "thermal_stability"],
    "garnet": ["ionic_conductivity", "interfacial_stability", "sintering_temperature"],
    "石榴石": ["ionic_conductivity", "interfacial_stability", "sintering_temperature"],
    "llzo": ["ionic_conductivity", "interfacial_stability", "sintering_temperature"],
    "interface": ["interfacial_stability", "contact_resistance"],
    "界面": ["interfacial_stability", "contact_resistance"],
    "doping": ["ionic_conductivity", "lattice_parameter", "activation_energy"],
    "掺杂": ["ionic_conductivity", "lattice_parameter", "activation_energy"],
    "stability": ["electrochemical_stability_window", "air_stability", "thermal_stability"],
    "稳定性": ["electrochemical_stability_window", "air_stability", "thermal_stability"],
}

# 调研阶段模板
PIPELINE_STEPS = [
    ("任务分解", "decompose_task", "研究问题拆解为可检索的子问题"),
    ("文献检索", "search_sci_base", "检索候选文献集"),
    ("文献筛选", "assess_relevance", "相关性评分与去重"),
    ("全文解析", "parse_pdf_with_mineru", "PDF版面分析与文本提取"),
    ("知识抽取", "extract_material_knowledge", "材料成分与性能数据抽取"),
    ("知识融合", "merge_extractions", "跨文献实体对齐与冲突检测"),
    ("Gap分析", "detect_property_conflicts", "研究空白识别"),
    ("假设生成", "generate_hypotheses", "可验证构效关系假设"),
    ("报告生成", "generate_report_structure", "结构化调研报告"),
]


@tool
def decompose_task(query: str) -> str:
    """将研究问题分解为可执行的子任务

    识别领域关键词，生成检索子问题、筛选标准、
    抽取目标与分析维度。

    Args:
        query: 研究问题

    Returns:
        子任务分解JSON
    """
    try:
        query_lower = query.lower()

        # 识别领域关键词
        matched_domains = [
            domain for domain in DOMAIN_PROPERTIES if domain in query_lower
        ]

        # 目标属性（去重保序）
        target_properties = []
        for domain in matched_domains:
            for prop in DOMAIN_PROPERTIES[domain]:
                if prop not in target_properties:
                    target_properties.append(prop)

        # 检索子问题：原问题 + 领域关键词组合
        search_queries = [query]
        for domain in matched_domains[:3]:
            search_queries.append(f"{query} {domain}")
        search_queries = list(dict.fromkeys(search_queries))

        # 筛选标准
        filter_criteria = [
            "标题或摘要包含目标材料/性能关键词",
            "有实验数据的原创研究优先于综述",
            "保留结论相互矛盾的文献（供Gap识别）",
        ]

        # 分析维度
        analysis_dimensions = [
            "材料成分-性能关系",
            "不同材料体系的性能对比",
            "性能数据一致性检验",
            "研究空白识别",
        ]

        return json.dumps(
            {
                "query": query,
                "detected_domains": matched_domains,
                "search_queries": search_queries,
                "target_properties": target_properties,
                "filter_criteria": filter_criteria,
                "analysis_dimensions": analysis_dimensions,
                "subtask_count": len(search_queries) + 3,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def create_research_plan(query: str, max_results: int = 10) -> str:
    """生成结构化调研计划

    Args:
        query: 研究问题
        max_results: 每步最大处理文献数

    Returns:
        调研计划JSON
    """
    try:
        # 先分解任务获取领域信息
        decompose_result = json.loads(
            decompose_task.invoke({"query": query})
        )

        steps = []
        for idx, (name, tool_name, goal) in enumerate(PIPELINE_STEPS, 1):
            steps.append({
                "step": idx,
                "name": name,
                "goal": goal,
                "tool": tool_name,
                "expected_output": (
                    "子任务清单与检索子问题"
                    if name == "任务分解"
                    else f"{name}阶段结果"
                ),
            })

        plan = {
            "query": query,
            "max_results": max_results,
            "detected_domains": decompose_result.get("detected_domains", []),
            "target_properties": decompose_result.get("target_properties", []),
            "steps": steps,
            "total_steps": len(steps),
        }
        return json.dumps(plan, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def estimate_scope(query: str) -> str:
    """评估调研范围：预估文献量与各阶段耗时

    Args:
        query: 研究问题

    Returns:
        范围评估JSON
    """
    try:
        decompose_result = json.loads(
            decompose_task.invoke({"query": query})
        )
        subtask_count = decompose_result.get("subtask_count", 4)
        domains = decompose_result.get("detected_domains", [])

        # 预估检索文献量：子任务越多、领域越聚焦，文献量越大
        base_papers = 50
        paper_estimate = base_papers + subtask_count * 20 + len(domains) * 30
        paper_estimate = min(paper_estimate, 300)

        return json.dumps(
            {
                "estimated_papers": paper_estimate,
                "estimated_steps": subtask_count + 5,
                "estimated_duration_minutes": 5 + subtask_count * 3,
                "confidence": (
                    "高" if len(domains) >= 2 else "中"
                ),
                "note": "预估基于领域关键词命中情况，实际取决于文献库覆盖度",
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def create_planner_agent(model: Optional[str] = None):
    """创建任务规划Agent

    负责研究问题分解与调研计划生成，
    作为多Agent系统的入口组件

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，任务规划Agent将以演示模式创建")
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
        tools=[decompose_task, create_research_plan, estimate_scope],
        system_prompt="""你是LitMat-Agent的任务规划模块，负责将用户研究问题分解为可执行的调研计划。

你可以使用以下工具：
1. decompose_task: 分解研究问题为检索子问题、筛选标准、抽取目标与分析维度
2. create_research_plan: 生成9阶段结构化调研计划
3. estimate_scope: 评估调研范围与预估耗时

规划原则：
- 优先识别材料体系（硫化物/氧化物/聚合物）与目标性能
- 子问题要相互独立且可检索
- 计划需覆盖检索→筛选→解析→抽取→融合→分析→报告全链路
- 目标属性需对应固态电解质关键指标（离子电导率、活化能、电化学窗口）""",
    )

    return agent


# 便捷函数
def get_default_planner_agent():
    """获取默认配置的任务规划Agent"""
    return create_planner_agent()
