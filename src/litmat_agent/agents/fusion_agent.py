"""知识融合Agent：跨文献实体对齐与冲突检测"""

import json
import re
from collections import defaultdict
from typing import Optional

from deepagents import create_deep_agent
from langchain_core.tools import tool

from litmat_agent.core.config import settings


def _normalize_formula(formula: str) -> str:
    """化学式规范化：去空格、统一大小写格式

    Args:
        formula: 原始化学式

    Returns:
        规范化后的化学式
    """
    # 去除空白与下划线
    normalized = re.sub(r"[\s_\-]+", "", formula)
    return normalized


@tool
def align_material_entities(materials_json: str) -> str:
    """跨文献材料实体对齐

    将多篇文献抽取的材料实体按化学式规范化后对齐合并，
    统计出现频次与来源文献。

    Args:
        materials_json: 材料实体列表JSON字符串（含formula/paper_title字段）

    Returns:
        对齐后的实体JSON
    """
    try:
        materials = json.loads(materials_json)
        aligned = {}

        for m in materials:
            formula = m.get("formula", "")
            if not formula:
                continue
            key = _normalize_formula(formula)
            if key not in aligned:
                aligned[key] = {
                    "canonical_formula": key,
                    "variants": set(),
                    "papers": set(),
                    "count": 0,
                }
            entry = aligned[key]
            entry["variants"].add(formula)
            if m.get("paper_title"):
                entry["papers"].add(m["paper_title"])
            entry["count"] += 1

        result = []
        for key, entry in aligned.items():
            result.append({
                "formula": key,
                "variants": sorted(entry["variants"]),
                "source_papers": sorted(entry["papers"]),
                "mention_count": entry["count"],
                "paper_count": len(entry["papers"]),
            })

        # 按提及次数排序
        result.sort(key=lambda x: x["mention_count"], reverse=True)

        return json.dumps({"aligned_materials": result}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def detect_property_conflicts(properties_json: str) -> str:
    """跨文献性能数据冲突检测

    对同一性能属性，比较不同文献的取值；
    差异超过10倍的标记为潜在矛盾，需核验实验条件。

    Args:
        properties_json: 性能数据列表JSON字符串（含property/value/unit/paper_title字段）

    Returns:
        冲突检测结果JSON
    """
    try:
        properties = json.loads(properties_json)
        groups = defaultdict(list)

        for p in properties:
            if isinstance(p.get("value"), (int, float)):
                groups[p.get("property", "unknown")].append(p)

        conflicts = []
        consistent = []

        for prop_name, values in groups.items():
            if len(values) < 2:
                consistent.append({
                    "property": prop_name,
                    "sample_count": len(values),
                    "note": "样本不足，无法检测冲突",
                })
                continue

            numeric = [v["value"] for v in values]
            vmax, vmin = max(numeric), min(numeric)

            if vmin > 0 and vmax / vmin >= 10:
                conflicts.append({
                    "property": prop_name,
                    "value_range": [vmin, vmax],
                    "max_ratio": round(vmax / vmin, 1),
                    "sources": [
                        {
                            "value": v["value"],
                            "unit": v.get("unit", ""),
                            "paper": v.get("paper_title", "unknown"),
                        }
                        for v in values
                    ],
                    "conflict_type": "magnitude_conflict",
                    "suggestion": "需核对测试条件（温度、压力、制备工艺）",
                })
            else:
                consistent.append({
                    "property": prop_name,
                    "value_range": [vmin, vmax],
                    "sample_count": len(values),
                    "note": "取值一致",
                })

        return json.dumps(
            {
                "conflicts": conflicts,
                "consistent_properties": consistent,
                "conflict_count": len(conflicts),
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def merge_extractions(extractions_json: str) -> str:
    """融合多篇文献的知识抽取结果

    输入多篇文献的抽取结果，输出融合后的统一知识视图：
    材料清单（对齐去重）+ 性能汇总（按材料分组）。

    Args:
        extractions_json: 抽取结果列表JSON字符串，
            每项含paper_title/materials/properties字段

    Returns:
        融合知识视图JSON
    """
    try:
        extractions = json.loads(extractions_json)

        all_materials = []
        all_properties = []

        for ext in extractions:
            paper_title = ext.get("paper_title", "unknown")
            for m in ext.get("materials", []):
                all_materials.append({**m, "paper_title": paper_title})
            for p in ext.get("properties", []):
                all_properties.append({**p, "paper_title": paper_title})

        # 实体对齐
        aligned_result = json.loads(
            align_material_entities.invoke(
                {"materials_json": json.dumps(all_materials, ensure_ascii=False)}
            )
        )
        # 冲突检测
        conflict_result = json.loads(
            detect_property_conflicts.invoke(
                {"properties_json": json.dumps(all_properties, ensure_ascii=False)}
            )
        )

        return json.dumps(
            {
                "materials": aligned_result.get("aligned_materials", []),
                "properties": all_properties,
                "conflicts": conflict_result.get("conflicts", []),
                "source_paper_count": len(extractions),
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def create_fusion_agent(model: Optional[str] = None):
    """创建知识融合Agent

    跨文献实体对齐、冲突检测与知识融合

    Args:
        model: 使用的LLM模型

    Returns:
        配置好的DeepAgent实例
    """
    model = model or settings.default_model

    # 检查API密钥，未配置时使用模拟模式
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("[提示] 未配置LLM API密钥，知识融合Agent将以演示模式创建")
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
        tools=[align_material_entities, detect_property_conflicts, merge_extractions],
        system_prompt="""你是LitMat-Agent的知识融合模块，负责跨文献知识对齐与融合。

你可以使用以下工具：
1. align_material_entities: 材料实体对齐（化学式规范化合并）
2. detect_property_conflicts: 性能数据冲突检测（差异>10倍标记矛盾）
3. merge_extractions: 融合多篇文献抽取结果，生成统一知识视图

融合原则：
- 同一材料的不同写法（如Li7La3Zr2O12 vs LLZO）需人工确认后合并
- 性能冲突必须标注来源文献与测试条件
- 区分"已确证事实"与"单一来源报道"
- 融合结果需保留证据溯源信息""",
    )

    return agent


# 便捷函数
def get_default_fusion_agent():
    """获取默认配置的知识融合Agent"""
    return create_fusion_agent()
