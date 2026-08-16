"""LangGraph工作流编排模块

注意：工具导入放在节点函数内部（延迟导入），
避免 tools <-> core 包之间的循环导入问题。
"""

import json
from collections import Counter, defaultdict
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class WorkflowState(TypedDict):
    """工作流状态定义"""

    # 输入
    query: str
    max_results: int

    # 检索阶段
    retrieved_papers: list[dict]
    filtered_papers: list[dict]

    # 解析阶段
    parsed_papers: list[dict]

    # 知识抽取阶段
    extracted_materials: list[dict]
    extracted_properties: list[dict]

    # 分析阶段
    research_gaps: list[dict]
    hypotheses: list[dict]

    # 输出
    report: str
    error: str

    # 消息历史
    messages: Annotated[list, add_messages]


class LiteratureWorkflow:
    """文献调研工作流"""

    def __init__(self):
        """初始化工作流"""
        self.workflow = StateGraph(WorkflowState)
        self._build_graph()

    def _build_graph(self):
        """构建工作流图"""
        # 添加节点
        self.workflow.add_node("retrieve", self._retrieve_node)
        self.workflow.add_node("filter", self._filter_node)
        self.workflow.add_node("parse", self._parse_node)
        self.workflow.add_node("extract", self._extract_node)
        self.workflow.add_node("analyze", self._analyze_node)
        self.workflow.add_node("generate_report", self._report_node)

        # 设置入口点
        self.workflow.set_entry_point("retrieve")

        # 添加边
        self.workflow.add_edge("retrieve", "filter")
        self.workflow.add_edge("filter", "parse")
        self.workflow.add_edge("parse", "extract")
        self.workflow.add_edge("extract", "analyze")
        self.workflow.add_edge("analyze", "generate_report")
        self.workflow.add_edge("generate_report", END)

        # 添加条件边（错误处理）
        self.workflow.add_conditional_edges(
            "retrieve",
            self._check_error,
            {"error": END, "continue": "filter"},
        )

    def _check_error(self, state: WorkflowState) -> Literal["error", "continue"]:
        """检查错误状态"""
        if state.get("error"):
            return "error"
        return "continue"

    # 节点函数（返回增量更新，避免 add_messages 重复合并）
    def _retrieve_node(self, state: WorkflowState) -> dict:
        """文献检索节点：调用Sci-Base本地检索"""
        try:
            from litmat_agent.tools.sci_base import search_sci_base

            result = search_sci_base.invoke({
                "query": state["query"],
                "max_results": state["max_results"],
            })
            papers = json.loads(result)
            if isinstance(papers, dict) and "error" in papers:
                return {
                    "retrieved_papers": [],
                    "messages": [("system", f"文献检索降级：{papers['error']}")],
                }
            return {
                "retrieved_papers": papers,
                "messages": [("system", f"文献检索完成：命中{len(papers)}篇")],
            }
        except Exception as e:
            return {
                "retrieved_papers": [],
                "messages": [("system", f"文献检索异常：{e}")],
            }

    def _filter_node(self, state: WorkflowState) -> dict:
        """文献筛选节点：按查询词相关性过滤"""
        try:
            query_words = [
                w for w in state["query"].lower().split() if len(w) > 2
            ]
            filtered = []
            for paper in state["retrieved_papers"]:
                text = (
                    str(paper.get("title", ""))
                    + " "
                    + str(paper.get("abstract", ""))
                ).lower()
                if not query_words or any(w in text for w in query_words):
                    filtered.append(paper)
            return {
                "filtered_papers": filtered,
                "messages": [
                    (
                        "system",
                        f"文献筛选完成：{len(filtered)}/{len(state['retrieved_papers'])}篇",
                    )
                ],
            }
        except Exception as e:
            return {
                "filtered_papers": state["retrieved_papers"],
                "messages": [("system", f"文献筛选降级：{e}")],
            }

    def _parse_node(self, state: WorkflowState) -> dict:
        """PDF解析节点：调用MinerU解析PDF或使用已有全文"""
        try:
            from litmat_agent.tools.pdf_parser import parse_pdf_with_mineru

            parsed = []
            for paper in state["filtered_papers"]:
                paper_copy = dict(paper)
                if paper.get("pdf_path"):
                    result = parse_pdf_with_mineru.invoke({
                        "pdf_path": paper["pdf_path"],
                    })
                    pdf_result = json.loads(result)
                    if "text" in pdf_result:
                        paper_copy["full_text"] = pdf_result["text"]
                    elif "error" in pdf_result:
                        paper_copy["parse_error"] = pdf_result["error"]
                parsed.append(paper_copy)
            return {
                "parsed_papers": parsed,
                "messages": [("system", f"PDF解析完成：{len(parsed)}篇")],
            }
        except Exception as e:
            return {
                "parsed_papers": [],
                "messages": [("system", f"PDF解析降级：{e}")],
            }

    def _extract_node(self, state: WorkflowState) -> dict:
        """知识抽取节点：调用材料知识抽取工具"""
        try:
            from litmat_agent.tools.knowledge_extraction import (
                extract_material_knowledge,
            )

            materials = []
            properties = []
            for paper in state["parsed_papers"]:
                text = paper.get("full_text") or paper.get("abstract") or ""
                if not text:
                    continue
                result = extract_material_knowledge.invoke({
                    "paper_text": text,
                })
                knowledge = json.loads(result)
                for m in knowledge.get("materials", []):
                    m["paper_title"] = paper.get("title", "")
                    materials.append(m)
                for p in knowledge.get("properties", []):
                    p["paper_title"] = paper.get("title", "")
                    properties.append(p)
            return {
                "extracted_materials": materials,
                "extracted_properties": properties,
                "messages": [
                    (
                        "system",
                        f"知识抽取完成：{len(materials)}个材料，{len(properties)}条性能数据",
                    )
                ],
            }
        except Exception as e:
            return {
                "extracted_materials": [],
                "extracted_properties": [],
                "messages": [("system", f"知识抽取异常：{e}")],
            }

    def _analyze_node(self, state: WorkflowState) -> dict:
        """分析节点：材料频率统计与性能冲突检测"""
        try:
            gaps = []
            hypotheses = []

            # 材料频率统计
            formula_counter = Counter(
                m.get("formula", "") for m in state["extracted_materials"]
            )
            for formula, freq in formula_counter.most_common(5):
                if freq >= 2:
                    hypotheses.append({
                        "type": "high_frequency_material",
                        "formula": formula,
                        "frequency": freq,
                        "note": f"{formula} 在{freq}篇文献中出现，值得重点关注",
                    })

            # 性能冲突检测：同一属性的取值差异
            prop_groups = defaultdict(list)
            for p in state["extracted_properties"]:
                prop_groups[p.get("property", "unknown")].append(p)

            for prop_name, values in prop_groups.items():
                numeric = [v["value"] for v in values if isinstance(v.get("value"), (int, float))]
                if len(numeric) >= 2:
                    vmax, vmin = max(numeric), min(numeric)
                    if vmin > 0 and vmax / vmin >= 10:
                        gaps.append({
                            "gap_type": "conflict",
                            "property": prop_name,
                            "value_range": [vmin, vmax],
                            "description": (
                                f"{prop_name} 在不同文献中取值差异超过10倍"
                                f"（{vmin} ~ {vmax}），可能存在矛盾结论或条件差异"
                            ),
                        })

            return {
                "research_gaps": gaps,
                "hypotheses": hypotheses,
                "messages": [
                    (
                        "system",
                        f"分析完成：{len(gaps)}个潜在Gap，{len(hypotheses)}条假设",
                    )
                ],
            }
        except Exception as e:
            return {
                "research_gaps": [],
                "hypotheses": [],
                "messages": [("system", f"分析异常：{e}")],
            }

    def _report_node(self, state: WorkflowState) -> dict:
        """报告生成节点：汇总生成结构化报告"""
        try:
            # 兼容元组与消息对象两种形式
            messages = []
            for m in state["messages"]:
                if isinstance(m, tuple):
                    messages.append(m[1])
                else:
                    messages.append(getattr(m, "content", str(m)))

            report = {
                "query": state["query"],
                "statistics": {
                    "retrieved": len(state["retrieved_papers"]),
                    "filtered": len(state["filtered_papers"]),
                    "parsed": len(state["parsed_papers"]),
                    "materials_extracted": len(state["extracted_materials"]),
                    "properties_extracted": len(state["extracted_properties"]),
                },
                "research_gaps": state["research_gaps"],
                "hypotheses": state["hypotheses"],
                "messages": messages,
            }
            if state.get("error"):
                report["error"] = state["error"]
            return {
                "report": json.dumps(report, ensure_ascii=False, indent=2),
                "messages": [("system", "报告生成完成")],
            }
        except Exception as e:
            return {
                "report": json.dumps({"error": str(e)}, ensure_ascii=False),
            }

    def compile(self):
        """编译工作流"""
        return self.workflow.compile()

    def run(self, query: str, max_results: int = 10) -> dict:
        """运行工作流

        Args:
            query: 研究问题
            max_results: 最大文献数

        Returns:
            工作流执行结果
        """
        app = self.compile()

        initial_state: WorkflowState = {
            "query": query,
            "max_results": max_results,
            "retrieved_papers": [],
            "filtered_papers": [],
            "parsed_papers": [],
            "extracted_materials": [],
            "extracted_properties": [],
            "research_gaps": [],
            "hypotheses": [],
            "report": "",
            "error": "",
            "messages": [],
        }

        result = app.invoke(initial_state)
        return result


# 便捷函数
def create_workflow() -> LiteratureWorkflow:
    """创建文献调研工作流"""
    return LiteratureWorkflow()
