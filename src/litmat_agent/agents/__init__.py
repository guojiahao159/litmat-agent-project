"""Agent模块：多Agent协作系统"""

from .literature_agent import create_literature_agent
from .research_agent import create_research_agent

__all__ = ["create_literature_agent", "create_research_agent"]
