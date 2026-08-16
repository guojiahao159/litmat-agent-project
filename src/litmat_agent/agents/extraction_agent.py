"""知识抽取Agent：材料成分识别与性能数据抽取"""

import json
from typing import Optional

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings


@tool
def extract_knowledge_from_text(paper_text: str, paper_title: str = "") -> str:
    """从文献文本中抽取材料知识与性能数据

    Args:
        paper_text: 文献全文或摘要
        paper_title: 文献标题（可选，用于溯源）

    Returns:
        抽取结果JSON（含materials/properties字段）
    """
    from litmat_agent.tools.knowledge_extraction import extract_material_knowledge

    try:
        result = json.loads(
            extract_material_knowledge.invoke({"paper_text": paper_text})
        )
        if paper_title:
            for m in result.get("materials", []):
                m["paper_title"] = paper_title
            for p in result.get("properties", []):
                p["paper_title"] = paper_title
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def normalize_property_units(properties_json: str) -> str:
    """性能数据单位统一（电导率换算为S/cm）

    Args:
        properties_json: 性能数据列表JSON字符串（含property/value/unit字段）

    Returns:
        单位统一后的数据JSON
    """
    from litmat_agent.tools.knowledge_extraction import normalize_units

    try:
        properties = json.loads(properties_json)
        for p in properties:
            unit = (p.get("unit") or "").lower()
            value = p.get("value")
            prop_name = (p.get("property") or "").lower()

            # 电导率类属性统一为S/cm
            if "conductivity" in prop_name and isinstance(value, (int, float)) and unit:
                try:
                    converted = json.loads(
                        normalize_units.invoke({
                            "value": float(value),
                            "unit": unit,
                            "category": "conductivity",
                        })
                    )
                    # normalize_units返回 {original, converted:{value, unit}}
                    if "converted" in converted:
                        p["value"] = converted["converted"]["value"]
                        p["unit"] = converted["converted"]["unit"]
                        p["normalized"] = True
                        continue
                except Exception:
                    pass
            p["normalized"] = False

        return json.dumps(properties, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def create_extraction_agent(model: Optional[str] = None):
    """创建知识抽取Agent

    专注材料成分识别、性能数据抽取与单位统一

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，知识抽取Agent将以演示模式创建")
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
        tools=[extract_knowledge_from_text, normalize_property_units],
        system_prompt="""你是LitMat-Agent的知识抽取模块，负责从文献文本中抽取结构化知识。

你可以使用以下工具：
1. extract_knowledge_from_text: 抽取材料化学式、成分、晶体结构与性能数据
2. normalize_property_units: 性能数据单位统一（如mS/cm→S/cm）

抽取原则：
- 材料化学式需保留原始写法（变体在融合阶段对齐）
- 性能数据必须含数值与单位，缺失单位的数据标记为待核验
- 只抽取原文明确陈述的信息，禁止推断
- 每条数据保留来源文献标题用于证据溯源""",
    )

    return agent


# 便捷函数
def get_default_extraction_agent():
    """获取默认配置的知识抽取Agent"""
    return create_extraction_agent()
