"""修复验证脚本：验证Agent工具绑定和工作流节点接入"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

print("=== 修复验证 ===")
print()

# 1. 验证工具兼容层
print("1. 工具兼容层验证")
from litmat_agent.tools.literature import (
    search_literature,
    extract_material_info,
    parse_pdf,
)

print(f"   - search_literature -> {search_literature.name}")
print(f"   - extract_material_info -> {extract_material_info.name}")
print(f"   - parse_pdf -> {parse_pdf.name}")

from litmat_agent.tools.retrieval import hybrid_search, rerank_results

print(f"   - hybrid_search -> {hybrid_search.name}")
print(f"   - rerank_results -> {rerank_results.name}")
print()

# 2. 验证Agent创建与工具绑定
print("2. Agent工具绑定验证（Mock模式）")
from litmat_agent.agents import create_literature_agent, create_research_agent

lit_agent = create_literature_agent()
research_agent = create_research_agent()
print("   - 文献调研Agent创建成功")
print("   - 研究分析Agent创建成功")
print()

# 3. 验证Agent源文件中的工具导入
print("3. Agent源文件工具绑定检查")
import inspect

from litmat_agent import agents

lit_src = inspect.getsource(agents.literature_agent)
checks = {
    "search_sci_base": "search_sci_base" in lit_src,
    "extract_material_knowledge": "extract_material_knowledge" in lit_src,
    "hybrid_search_advanced": "hybrid_search_advanced" in lit_src,
    "parse_pdf_with_mineru": "parse_pdf_with_mineru" in lit_src,
    "旧占位工具search_literature": "search_literature" in lit_src,
}
for name, result in checks.items():
    print(f"   - {name}: {'✓' if result else '✗'}")
print()

# 4. 工作流节点接入验证
print("4. 工作流节点验证")
from litmat_agent.core.workflow import LiteratureWorkflow

wf = LiteratureWorkflow()
print("   - 工作流创建成功")

# 检查节点函数源码中是否调用了真实工具
wf_src = inspect.getsource(LiteratureWorkflow)
wf_checks = {
    "_retrieve_node调用search_sci_base": "search_sci_base.invoke" in wf_src,
    "_parse_node调用parse_pdf_with_mineru": "parse_pdf_with_mineru.invoke" in wf_src,
    "_extract_node调用extract_material_knowledge": "extract_material_knowledge.invoke" in wf_src,
    "_analyze_node冲突检测": "conflict" in wf_src,
    "_report_node生成JSON报告": "json.dumps(report" in wf_src,
}
for name, result in wf_checks.items():
    print(f"   - {name}: {'✓' if result else '✗'}")
print()

# 5. 端到端工作流运行测试
print("5. 端到端工作流运行")
try:
    result = wf.run(query="sulfide solid electrolyte", max_results=5)
    import json

    report = json.loads(result.get("report", "{}"))
    stats = report.get("statistics", {})
    print(f"   - 工作流执行完成")
    print(f"   - 统计: 检索{stats.get('retrieved')} 筛选{stats.get('filtered')} "
          f"解析{stats.get('parsed')} 抽取材料{stats.get('materials_extracted')}")
    print(f"   - 消息数: {len(result.get('messages', []))}")
    msg_texts = []
    for m in result.get("messages", []):
        if isinstance(m, tuple):
            msg_texts.append(m[1])
        else:
            msg_texts.append(getattr(m, "content", str(m)))
    print(f"   - 消息链: {msg_texts}")
except Exception as e:
    print(f"   - 工作流运行异常: {e}")
print()

print("=== 修复验证完成 ===")
