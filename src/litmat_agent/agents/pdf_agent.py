"""PDF解析Agent：全文结构化解析"""

import json
from typing import Optional

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings


@tool
def parse_pdf_with_mineru_tool(pdf_path: str) -> str:
    """使用MinerU解析PDF文件

    Args:
        pdf_path: PDF文件路径

    Returns:
        解析结果JSON（含结构化文本或错误信息）
    """
    # 复用已有PDF解析工具（避免循环导入，延迟导入）
    from litmat_agent.tools.pdf_parser import parse_pdf_with_mineru

    return parse_pdf_with_mineru.invoke({"pdf_path": pdf_path})


@tool
def batch_parse_pdfs(pdf_paths_json: str) -> str:
    """批量解析PDF文件

    Args:
        pdf_paths_json: PDF路径列表JSON字符串

    Returns:
        批量解析结果JSON
    """
    from litmat_agent.tools.pdf_parser import parse_pdf_with_mineru

    try:
        paths = json.loads(pdf_paths_json)
        results = []
        for path in paths:
            result = json.loads(
                parse_pdf_with_mineru.invoke({"pdf_path": path})
            )
            result["pdf_path"] = path
            results.append(result)
        return json.dumps(
            {
                "total": len(paths),
                "success": sum(1 for r in results if "text" in r),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def create_pdf_agent(model: Optional[str] = None):
    """创建PDF解析Agent

    专注PDF全文结构化解析（MinerU版面分析+文本提取）

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，PDF解析Agent将以演示模式创建")
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
        tools=[parse_pdf_with_mineru_tool, batch_parse_pdfs],
        system_prompt="""你是LitMat-Agent的PDF解析模块，负责将PDF文献解析为结构化全文。

你可以使用以下工具：
1. parse_pdf_with_mineru_tool: 使用MinerU解析单个PDF文件
2. batch_parse_pdfs: 批量解析多个PDF文件

解析原则：
- 保留版面结构（标题、段落、表格、公式）
- 解析失败时报告错误原因而非静默跳过
- 提取的全文文本供知识抽取模块使用""",
    )

    return agent


# 便捷函数
def get_default_pdf_agent():
    """获取默认配置的PDF解析Agent"""
    return create_pdf_agent()
