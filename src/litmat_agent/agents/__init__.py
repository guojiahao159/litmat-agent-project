"""Agent模块：多Agent协作系统

包含9个专业化Agent（完整覆盖方案要求）：
- planner_agent: 任务规划（问题分解+调研计划）
- literature_agent: 文献检索（多源检索+聚合）
- filter_agent: 文献筛选（相关性评估+去重）
- pdf_agent: PDF解析（MinerU版面分析+文本提取）
- extraction_agent: 知识抽取（成分/性能抽取+单位统一）
- fusion_agent: 知识融合（实体对齐+冲突检测）
- research_agent: Gap识别（构效关系+假设生成）
- verification_agent: 证据核验（引用链追踪+原文定位）
- report_agent: 报告生成（结构化Markdown报告）
"""

from .extraction_agent import create_extraction_agent, get_default_extraction_agent
from .filter_agent import create_filter_agent, get_default_filter_agent
from .fusion_agent import create_fusion_agent, get_default_fusion_agent
from .literature_agent import create_literature_agent, get_default_agent
from .pdf_agent import create_pdf_agent, get_default_pdf_agent
from .planner_agent import create_planner_agent, get_default_planner_agent
from .report_agent import create_report_agent, get_default_report_agent
from .research_agent import create_research_agent
from .verification_agent import (
    create_verification_agent,
    get_default_verification_agent,
)

__all__ = [
    "create_planner_agent",
    "create_literature_agent",
    "create_filter_agent",
    "create_pdf_agent",
    "create_extraction_agent",
    "create_fusion_agent",
    "create_research_agent",
    "create_verification_agent",
    "create_report_agent",
    "get_default_planner_agent",
    "get_default_agent",
    "get_default_filter_agent",
    "get_default_pdf_agent",
    "get_default_extraction_agent",
    "get_default_fusion_agent",
    "get_default_verification_agent",
    "get_default_report_agent",
]
