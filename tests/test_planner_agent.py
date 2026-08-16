"""任务规划Agent验证脚本：工具、Agent创建、工作流接入"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

print("=== 任务规划Agent验证 ===")
print()

# 1. 任务分解工具
print("1. 任务分解工具")
from litmat_agent.agents.planner_agent import (
    decompose_task,
    create_research_plan,
    estimate_scope,
    create_planner_agent,
)

query = "硫化物固态电解质的离子电导率影响因素"
decompose_result = json.loads(decompose_task.invoke({"query": query}))
print(f"   - 识别领域: {decompose_result.get('detected_domains')}")
print(f"   - 检索子问题数: {len(decompose_result.get('search_queries', []))}")
print(f"   - 目标属性: {decompose_result.get('target_properties')}")
assert len(decompose_result.get("search_queries", [])) >= 1, "子问题生成失败"
print("   ✓ 任务分解通过")
print()

# 2. 调研计划工具
print("2. 调研计划工具")
plan_result = json.loads(
    create_research_plan.invoke({"query": query, "max_results": 10})
)
steps = plan_result.get("steps", [])
print(f"   - 计划步骤数: {plan_result.get('total_steps')}")
print(f"   - 步骤清单: {[s['name'] for s in steps]}")
assert plan_result.get("total_steps") == 9, "计划步骤数应为9"
print("   ✓ 调研计划通过")
print()

# 3. 范围评估工具
print("3. 范围评估工具")
scope_result = json.loads(estimate_scope.invoke({"query": query}))
print(f"   - 预估文献量: {scope_result.get('estimated_papers')}篇")
print(f"   - 预估耗时: {scope_result.get('estimated_duration_minutes')}分钟")
print(f"   - 置信度: {scope_result.get('confidence')}")
print("   ✓ 范围评估通过")
print()

# 4. 规划Agent创建（Mock模式）
print("4. 任务规划Agent创建")
planner_agent = create_planner_agent()
print("   ✓ 规划Agent创建成功（Mock模式）")
print()

# 5. 全部6个Agent可用
print("5. 全部6个Agent导入")
from litmat_agent.agents import (
    create_planner_agent as import_planner,
    create_literature_agent,
    create_filter_agent,
    create_fusion_agent,
    create_research_agent,
    create_report_agent,
)

all_agents = [
    ("任务规划", import_planner),
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

# 6. 工作流plan节点接入验证
print("6. 工作流plan节点接入")
from litmat_agent.core.workflow import create_workflow

workflow = create_workflow()
result = workflow.run(query=query, max_results=5)
messages = []
for m in result.get("messages", []):
    if isinstance(m, tuple):
        messages.append(m[1])
    else:
        messages.append(getattr(m, "content", str(m)))

plan_msg = [m for m in messages if "任务规划" in m]
print(f"   - 规划节点消息: {plan_msg[0] if plan_msg else '未找到'}")
assert plan_msg, "plan节点消息缺失"

# 检查plan状态
plan = result.get("plan", {})
print(f"   - plan状态字段: query={plan.get('query', '')[:20]}..., domains={plan.get('detected_domains')}")

# 消息序列：规划 → 检索 → 筛选 → 解析 → 抽取 → 分析 → 报告
print(f"   - 全部消息数: {len(messages)}")
for msg in messages:
    print(f"     · {msg[:50]}")
print()

print("=== 任务规划Agent验证完成 ===")
