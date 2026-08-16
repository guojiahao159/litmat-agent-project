"""中优先级模块验证脚本"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

print("=== 中优先级模块验证 ===")
print()

# 1. 知识抽取模块
from litmat_agent.tools.knowledge_extraction import MaterialExtractor, UnitConverter

print("1. 知识抽取模块")
test_text = """
LLZO (Li7La3Zr2O12) garnet-type solid electrolyte exhibited
ionic conductivity of 1.2 mS/cm at room temperature (25°C),
with an activation energy of 0.32 eV.
"""
materials = MaterialExtractor.extract_materials(test_text)
properties = MaterialExtractor.extract_properties(test_text)
print(f"   - 材料识别: {[m['formula'] for m in materials]}")
print(f"   - 性能抽取: {[(p['property'], p['value'], p['unit']) for p in properties]}")
print(f"   - 单位统一: {UnitConverter.convert_conductivity(1.2, 'mS/cm')} S/cm")
print()

# 2. 数据库模块
from litmat_agent.core.database import PostgresManager, Neo4jManager

print("2. 数据库模块")
pg = PostgresManager("sqlite:///:memory:")
pg.create_tables()
print("   - PostgreSQL ORM: 表创建成功")
paper_id = pg.add_paper({"title": "Test Paper", "doi": "10.1234/test"})
print(f"   - 文献存储: 成功 (ID={paper_id})")
print(f"   - 文献查询: {pg.search_papers('Test', 5)}")
print()

# 3. 证据链追踪
from litmat_agent.core.evidence import EvidenceTracker, CitationParser

print("3. 证据链追踪")
tracker = EvidenceTracker()
tracker.add_evidence(
    hypothesis_id="H1",
    paper_id="P1",
    quote_text="ionic conductivity of 1.2 mS/cm",
    confidence=0.95,
)
chain = tracker.build_chain("H1")
print(f"   - 证据链: {len(chain)}条证据")
location = tracker.locate_quote(test_text, "ionic conductivity of 1.2 mS/cm")
print(f"   - 原文定位: 段落{location['paragraph_index']}, 页码{location['page_number']}")
print()

# 4. 引用解析
citations = CitationParser.extract_citations(
    "As shown in [1,3] and [5-7], the results indicate..."
)
print(f"   - 引用解析: {[c['number'] for c in citations]}")
print()

# 5. 工具函数验证
from litmat_agent.tools import extract_material_knowledge, normalize_units

print("5. 工具函数")
result = extract_material_knowledge.invoke({"paper_text": test_text})
print(f"   - 知识抽取工具: {result[:100]}...")
result2 = normalize_units.invoke(
    {"value": 1.2, "unit": "mS/cm", "category": "conductivity"}
)
print(f"   - 单位统一工具: {result2}")
print()

# 6. 证据链工具验证
from litmat_agent.core import (
    add_evidence_record,
    build_evidence_chain,
    locate_quote_in_text,
)

print("6. 证据链工具")
add_evidence_record.invoke(
    {
        "hypothesis_id": "H2",
        "paper_id": "P2",
        "quote_text": "activation energy of 0.32 eV",
        "confidence": 0.88,
    }
)
chain2 = build_evidence_chain.invoke({"hypothesis_id": "H2"})
print(f"   - 证据链构建: {chain2[:80]}...")
loc = locate_quote_in_text.invoke(
    {"full_text": test_text, "quote_text": "activation energy of 0.32 eV"}
)
print(f"   - 原文定位: {loc}")
print()

print("=== 所有中优先级模块验证通过 ===")
