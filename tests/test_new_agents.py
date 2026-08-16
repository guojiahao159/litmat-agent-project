"""新组件验证脚本：Sciverse客户端 + 3个新Agent"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

print("=== 新组件验证 ===")
print()

# 1. Sciverse API客户端
print("1. Sciverse API客户端")
from litmat_agent.tools.sciverse import (
    SciverseClient,
    get_sciverse_client,
    search_sciverse,
    get_sciverse_metadata,
    locate_evidence_sciverse,
)

client = get_sciverse_client()
print(f"   - 客户端创建成功，已配置: {client.configured}")
print(f"   - 基础URL: {client.base_url}")

# 未配置API Key时应优雅降级
result = search_sciverse.invoke({"query": "sulfide solid electrolyte", "max_results": 5})
import json

r = json.loads(result)
print(f"   - 未配置Key降级: {'✓' if ('error' in r or 'results' in r) else '✗'}")
print()

# 2. 文献筛选Agent工具
print("2. 文献筛选Agent工具")
from litmat_agent.agents.filter_agent import (
    assess_relevance,
    deduplicate_papers,
    filter_by_threshold,
)

test_papers = [
    {
        "title": "High ionic conductivity in sulfide solid electrolytes",
        "abstract": "Li6PS5Cl exhibits ionic conductivity of 3.2 mS/cm",
        "doi": "10.1000/test1",
    },
    {
        "title": "Polymer electrolytes for batteries",
        "abstract": "PEO based electrolytes show moderate conductivity",
        "doi": "10.1000/test2",
    },
    {
        "title": "High ionic conductivity in sulfide solid electrolytes",
        "abstract": "Li6PS5Cl exhibits ionic conductivity of 3.2 mS/cm",
    },
]
rel_result = json.loads(
    assess_relevance.invoke(
        {
            "paper_metadata": json.dumps(test_papers[0], ensure_ascii=False),
            "query": "sulfide solid electrolyte conductivity",
        }
    )
)
print(f"   - 相关性评分: {rel_result.get('relevance_score')} (匹配词: {rel_result.get('matched_keywords')})")

dedup_result = json.loads(
    deduplicate_papers.invoke(
        {"papers_json": json.dumps(test_papers, ensure_ascii=False)}
    )
)
print(f"   - 去重: 原始{dedup_result.get('original_count')}篇 → 保留{len(dedup_result.get('papers', []))}篇，去除{dedup_result.get('removed_duplicates')}篇")
print()

# 3. 知识融合Agent工具
print("3. 知识融合Agent工具")
from litmat_agent.agents.fusion_agent import (
    align_material_entities,
    detect_property_conflicts,
    merge_extractions,
)

test_materials = [
    {"formula": "Li6PS5Cl", "paper_title": "Paper A"},
    {"formula": "Li6 PS5 Cl", "paper_title": "Paper B"},
    {"formula": "Li6PS5Cl", "paper_title": "Paper A"},
    {"formula": "Li7La3Zr2O12", "paper_title": "Paper C"},
]
align_result = json.loads(
    align_material_entities.invoke(
        {"materials_json": json.dumps(test_materials, ensure_ascii=False)}
    )
)
print(f"   - 实体对齐: {len(align_result.get('aligned_materials', []))}个唯一实体")
for m in align_result.get("aligned_materials", []):
    print(f"     {m['formula']}: {m['mention_count']}次提及, {m['paper_count']}篇文献")

test_properties = [
    {"property": "ionic_conductivity", "value": 3.2, "unit": "mS/cm", "paper_title": "Paper A"},
    {"property": "ionic_conductivity", "value": 0.01, "unit": "mS/cm", "paper_title": "Paper B"},
    {"property": "activation_energy", "value": 0.32, "unit": "eV", "paper_title": "Paper A"},
]
conflict_result = json.loads(
    detect_property_conflicts.invoke(
        {"properties_json": json.dumps(test_properties, ensure_ascii=False)}
    )
)
print(f"   - 冲突检测: {conflict_result.get('conflict_count')}个冲突")
for c in conflict_result.get("conflicts", []):
    print(f"     {c['property']}: {c['value_range']} (比值{c['max_ratio']}倍)")
print()

# 4. 报告生成Agent工具
print("4. 报告生成Agent工具")
from litmat_agent.agents.report_agent import (
    generate_report_structure,
    format_references,
    summarize_findings,
)

report = generate_report_structure.invoke(
    {
        "query": "硫化物固态电解质的离子电导率影响因素",
        "retrieved_count": 120,
        "filtered_count": 45,
        "material_count": 12,
        "property_count": 30,
        "materials": "Li6PS5Cl（最高离子电导率3.2 mS/cm）",
        "gaps": "卤素掺杂对晶界阻抗的影响机制尚不明确",
        "hypotheses": "Cl掺杂降低晶界阻抗，与S空位浓度正相关",
        "evidence": "[1] 3.2 mS/cm @ 25°C（DOI: 10.1000/test1）",
        "conclusions": "建议优先研究Cl/Br混合掺杂体系",
    }
)
print(f"   - 报告生成: {'✓' if report.startswith('# 文献调研报告') else '✗'}")
print(f"   - 报告长度: {len(report)}字符")

refs = format_references.invoke(
    {
        "references_json": json.dumps(
            [
                {
                    "title": "High ionic conductivity in sulfide electrolytes",
                    "authors": ["Zhang Y", "Wang L", "Li X"],
                    "year": 2023,
                    "journal": "Nature Materials",
                    "doi": "10.1000/nm.2023.001",
                }
            ],
            ensure_ascii=False,
        ),
        "style": "numbered",
    }
)
print(f"   - 参考文献格式化: {refs}")

summary = summarize_findings.invoke(
    {
        "analysis_json": json.dumps(
            {
                "research_gaps": [
                    {"description": "卤素掺杂机制不明确", "gap_type": "unknown"}
                ],
                "hypotheses": [
                    {"note": "Cl掺杂降低晶界阻抗", "type": "doping"}
                ],
            },
            ensure_ascii=False,
        )
    }
)
print(f"   - 结论摘要: {summary[:60]}...")
print()

# 5. 三个新Agent创建
print("5. 三个新Agent创建（Mock模式）")
from litmat_agent.agents import (
    create_filter_agent,
    create_fusion_agent,
    create_report_agent,
)

filter_agent = create_filter_agent()
fusion_agent = create_fusion_agent()
report_agent = create_report_agent()
print("   - 文献筛选Agent ✓")
print("   - 知识融合Agent ✓")
print("   - 报告生成Agent ✓")
print()

# 6. 全部5个Agent可用
print("6. 全部5个Agent导入")
from litmat_agent.agents import (
    create_literature_agent,
    create_research_agent,
)

all_agents = [
    ("文献调研", create_literature_agent),
    ("文献筛选", create_filter_agent),
    ("知识融合", create_fusion_agent),
    ("研究分析", create_research_agent),
    ("报告生成", create_report_agent),
]
for name, factory in all_agents:
    agent = factory()
    print(f"   - {name}Agent: ✓")
print()

print("=== 新组件验证完成 ===")
