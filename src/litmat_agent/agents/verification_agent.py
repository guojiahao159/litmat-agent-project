"""证据核验Agent：文献溯源与事实核验"""

from typing import Optional

from deepagents import create_deep_agent

from litmat_agent.core.config import settings
from litmat_agent.core.evidence import (
    add_evidence_record,
    build_evidence_chain,
    extract_citation_chain,
    locate_quote_in_text,
    verify_evidence_chain,
)


def create_verification_agent(model: Optional[str] = None):
    """创建证据核验Agent

    专注引用链追踪、原文定位与事实核验

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，证据核验Agent将以演示模式创建")
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
            add_evidence_record,
            build_evidence_chain,
            locate_quote_in_text,
            verify_evidence_chain,
            extract_citation_chain,
        ],
        system_prompt="""你是LitMat-Agent的证据核验模块，负责文献溯源与事实核验。

你可以使用以下工具：
1. add_evidence_record: 为假设添加证据记录（含引用原文与置信度）
2. build_evidence_chain: 构建假设的完整证据链（按置信度排序）
3. locate_quote_in_text: 在原文中定位引用片段（页码/段落/上下文）
4. verify_evidence_chain: 验证证据链完整性（核验原文是否真的支持结论）
5. extract_citation_chain: 从正文提取引用编号并关联参考文献列表

核验原则：
- 每个结论必须能追溯到具体文献与原文片段
- 引用片段必须与结论语义一致（禁止断章取义）
- 无法定位原文的证据标记为"未验证"并降低置信度
- 证据链需覆盖Gap与假设的全部关键断言""",
    )

    return agent


# 便捷函数
def get_default_verification_agent():
    """获取默认配置的证据核验Agent"""
    return create_verification_agent()
