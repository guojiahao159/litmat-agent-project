"""LitMat-Agent Streamlit交互界面

启动方式：
    uv run streamlit run app.py
"""

import json
import sys
from pathlib import Path

# 确保项目根目录在导入路径中
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from litmat_agent.core.config import settings

st.set_page_config(
    page_title="LitMat-Agent 文献调研系统",
    layout="wide",
)

# ========== 侧边栏：系统状态 ==========
with st.sidebar:
    st.title("系统状态")

    st.subheader("LLM 配置")
    if settings.openai_api_key or settings.anthropic_api_key:
        st.success("LLM API 已配置")
    else:
        st.warning("未配置 LLM API（演示模式）")
        st.caption("Agent 仅展示结构，工作流可运行")

    st.subheader("数据源配置")
    st.caption(f"Sci-Base 路径: {settings.sci_base_data_path}")
    st.caption(f"PostgreSQL: {settings.postgres_url}")
    st.caption(f"Neo4j: {settings.neo4j_uri}")
    st.caption(f"Sciverse: {settings.sciverse_base_url}")
    st.caption("Sciverse Key: " + ("已配置" if settings.sciverse_api_key else "未配置"))

    st.subheader("Agent 清单")
    agents = [
        "1. 任务规划 Agent（问题分解+计划）",
        "2. 文献调研 Agent（检索+抽取）",
        "3. 文献筛选 Agent（相关性+去重）",
        "4. 知识融合 Agent（对齐+冲突检测）",
        "5. 研究分析 Agent（构效关系+假设）",
        "6. 报告生成 Agent（结构化报告）",
    ]
    for agent in agents:
        st.caption(agent)

    st.divider()
    st.caption("LitMat-Agent v0.1.0")
    st.caption("面向固态电解质研发的文献驱动科学发现智能体")

# ========== 主界面 ==========
st.title("LitMat-Agent")
st.markdown("**面向固态电解质研发的文献驱动科学发现智能体系统**")

st.divider()

# 查询输入区
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "研究问题",
        placeholder="例如：硫化物固态电解质的离子电导率影响因素有哪些？",
    )
with col2:
    max_results = st.number_input("最大检索数", min_value=5, max_value=100, value=10)

run_clicked = st.button("开始调研", type="primary", use_container_width=True)

# 示例查询快捷按钮
st.caption("示例查询：")
example_cols = st.columns(3)
examples = [
    "硫化物固态电解质离子电导率",
    "LLZO石榴石型电解质掺杂改性",
    "聚合物电解质PEO界面稳定性",
]
for col, example in zip(example_cols, examples):
    if col.button(example, use_container_width=True):
        query = example
        st.session_state["query"] = example
        run_clicked = True

# ========== 执行调研 ==========
if run_clicked:
    if not query:
        st.error("请输入研究问题")
    else:
        with st.spinner("调研进行中，正在执行检索-筛选-解析-抽取-分析-报告全流程..."):
            try:
                from litmat_agent.core.workflow import create_workflow

                workflow = create_workflow()
                result = workflow.run(query=query, max_results=max_results)

                # 解析报告
                report = json.loads(result.get("report", "{}"))

                # 保存到会话状态供后续展示
                st.session_state["result"] = result
                st.session_state["report"] = report

            except Exception as e:
                st.error(f"调研执行失败: {e}")
                report = None
                result = None

        # ========== 结果展示 ==========
        if result is not None:
            tab_report, tab_stats, tab_gaps, tab_hypotheses, tab_log = st.tabs(
                ["调研报告", "统计概览", "研究空白", "候选假设", "执行日志"]
            )

            with tab_report:
                if report.get("error"):
                    st.warning(f"报告生成异常: {report['error']}")
                else:
                    st.markdown(f"## 调研报告")
                    st.markdown(f"**研究问题**: {report.get('query', query)}")
                    st.divider()

                    # 调研概况
                    stats = report.get("statistics", {})
                    st.markdown("### 调研概况")
                    metric_cols = st.columns(5)
                    metric_cols[0].metric("检索文献", stats.get("retrieved", 0))
                    metric_cols[1].metric("筛选相关", stats.get("filtered", 0))
                    metric_cols[2].metric("解析文献", stats.get("parsed", 0))
                    metric_cols[3].metric("材料实体", stats.get("materials_extracted", 0))
                    metric_cols[4].metric("性能数据", stats.get("properties_extracted", 0))
                    st.divider()

                    # 研究空白
                    st.markdown("### 研究空白")
                    gaps = report.get("research_gaps", [])
                    if gaps:
                        for i, gap in enumerate(gaps, 1):
                            st.markdown(f"**{i}. [{gap.get('gap_type', '')}] {gap.get('property', '')}**")
                            st.markdown(gap.get("description", ""))
                            if gap.get("value_range"):
                                st.caption(f"取值区间: {gap['value_range']}")
                    else:
                        st.info("未发现显著研究空白（可增大检索范围重试）")
                    st.divider()

                    # 候选假设
                    st.markdown("### 候选假设")
                    hypotheses = report.get("hypotheses", [])
                    if hypotheses:
                        for i, hyp in enumerate(hypotheses, 1):
                            st.markdown(f"**{i}. {hyp.get('formula', hyp.get('type', ''))}**")
                            st.markdown(hyp.get("note", ""))
                    else:
                        st.info("暂未生成候选假设")

            with tab_stats:
                st.markdown("### 统计概览")
                stats = report.get("statistics", {})
                stats_df = {
                    "指标": ["检索文献数", "筛选相关数", "解析文献数", "材料实体数", "性能数据数"],
                    "数值": [
                        stats.get("retrieved", 0),
                        stats.get("filtered", 0),
                        stats.get("parsed", 0),
                        stats.get("materials_extracted", 0),
                        stats.get("properties_extracted", 0),
                    ],
                }
                st.dataframe(stats_df, use_container_width=True)

                # 材料清单
                if result.get("extracted_materials"):
                    st.markdown("### 抽取的材料实体")
                    materials = result["extracted_materials"]
                    material_df = {
                        "化学式": [m.get("formula", "") for m in materials],
                        "出现次数": [m.get("count", 1) for m in materials],
                        "来源文献": [m.get("paper_title", "")[:40] for m in materials],
                    }
                    st.dataframe(material_df, use_container_width=True)

                # 性能数据
                if result.get("extracted_properties"):
                    st.markdown("### 抽取的性能数据")
                    properties = result["extracted_properties"]
                    prop_df = {
                        "性能": [p.get("property", "") for p in properties],
                        "数值": [p.get("value", "") for p in properties],
                        "单位": [p.get("unit", "") for p in properties],
                        "来源文献": [p.get("paper_title", "")[:40] for p in properties],
                    }
                    st.dataframe(prop_df, use_container_width=True)

            with tab_gaps:
                st.markdown("### 研究空白详情")
                gaps = report.get("research_gaps", [])
                if gaps:
                    for i, gap in enumerate(gaps, 1):
                        with st.expander(f"Gap {i}: {gap.get('property', gap.get('gap_type', ''))}"):
                            st.json(gap)
                else:
                    st.info("未发现显著研究空白")

            with tab_hypotheses:
                st.markdown("### 候选假设详情")
                hypotheses = report.get("hypotheses", [])
                if hypotheses:
                    for i, hyp in enumerate(hypotheses, 1):
                        with st.expander(f"假设 {i}: {hyp.get('formula', hyp.get('type', ''))}"):
                            st.json(hyp)
                else:
                    st.info("暂未生成候选假设")

            with tab_log:
                st.markdown("### 执行日志")
                messages = report.get("messages", [])
                for msg in messages:
                    st.caption(f"- {msg}")

else:
    # 未运行时显示说明
    st.info("输入研究问题后点击「开始调研」，系统将自动执行：检索 → 筛选 → 解析 → 抽取 → 分析 → 报告 全流程。")
    st.markdown(
        """
### 系统能力
| 阶段 | 组件 | 技术实现 |
|------|------|---------|
| 任务规划 | 规划Agent | 问题分解 + 9阶段调研计划 |
| 文献检索 | Sci-Base + Sciverse | Elasticsearch + 实时API |
| 文献筛选 | 筛选Agent | 相关性评分 + DOI去重 |
| PDF解析 | MinerU | 版面分析 + 文本提取 |
| 知识抽取 | 抽取工具 | 材料成分 + 性能数据 + 单位统一 |
| 知识融合 | 融合Agent | 实体对齐 + 冲突检测 |
| 分析假设 | 研究分析Agent | 构效关系 + Gap识别 |
| 报告生成 | 报告Agent | 结构化Markdown报告 |

> 提示：未配置LLM API密钥时，工作流（检索-筛选-解析-抽取-分析）仍可运行，
> Agent推理能力需配置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY。
        """
    )
