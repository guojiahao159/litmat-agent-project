"""研究分析Agent：构效关系发现"""

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings
from litmat_agent.tools import extract_material_knowledge, search_sci_base


@tool
def analyze_structure_property(material_data: str) -> str:
    """分析材料构效关系

    Args:
        material_data: 材料结构-性能数据

    Returns:
        构效关系分析结果
    """
    return "构效关系分析（待实现）"


@tool
def generate_hypothesis(gap_analysis: str) -> str:
    """基于Research Gap生成可验证假设

    Args:
        gap_analysis: Research Gap分析结果

    Returns:
        科学假设
    """
    return "假设生成（待实现）"


@tool
def suggest_validation(hypothesis: str) -> str:
    """建议假设验证方法

    Args:
        hypothesis: 科学假设

    Returns:
        验证方法建议
    """
    return "验证方法建议（待实现）"


def create_research_agent(model: str = None):
    """创建研究分析Agent

    专注于构效关系发现和科学假设生成

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，研究分析Agent将以演示模式创建")
        # 返回一个模拟的Agent对象，仅用于演示结构
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
        tools=[
            search_sci_base,
            extract_material_knowledge,
            analyze_structure_property,
            generate_hypothesis,
            suggest_validation,
        ],
        system_prompt="""你是LitMat-Agent的研究分析模块，专注于固态电解质的构效关系发现。

你可以使用以下工具完成分析任务：
1. search_sci_base: 检索Sci-Base本地文献库（关键词+向量检索）
2. extract_material_knowledge: 从文献文本抽取材料成分、性能数据（自动单位统一）

你的核心任务：
1. 分析材料的成分-结构-性能关联
2. 识别文献中的矛盾结论和知识空白
3. 基于证据生成可验证的科学假设
4. 建议实验或计算方法验证假设

请确保：
- 每个假设都有明确的文献证据支撑
- 区分已验证的事实和推测性结论
- 假设必须是可证伪的
- 建议的验证方法必须具体可行""",
    )

    return agent
