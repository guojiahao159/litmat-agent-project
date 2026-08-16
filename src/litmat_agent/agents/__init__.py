"""Agent模块：多Agent协作系统

包含6个专业化Agent：
- planner_agent: 任务规划（问题分解+调研计划）
- literature_agent: 文献调研（检索+抽取+Gap初筛）
- filter_agent: 文献筛选（相关性评估+去重）
- fusion_agent: 知识融合（实体对齐+冲突检测）
- research_agent: 研究分析（构效关系+假设生成）
- report_agent: 报告生成（结构化Markdown报告）
"""

from .filter_agent import create_filter_agent, get_default_filter_agent
from .fusion_agent import create_fusion_agent, get_default_fusion_agent
from .literature_agent import create_literature_agent, get_default_agent
from .planner_agent import create_planner_agent, get_default_planner_agent
from .report_agent import create_report_agent, get_default_report_agent
from .research_agent import create_research_agent

__all__ = [
    "create_planner_agent",
    "create_literature_agent",
    "create_filter_agent",
    "create_fusion_agent",
    "create_research_agent",
    "create_report_agent",
    "get_default_planner_agent",
    "get_default_agent",
    "get_default_filter_agent",
    "get_default_fusion_agent",
    "get_default_report_agent",
]
