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

    # 任务规划阶段
    plan: dict

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

    # 证据核验阶段
    evidence_chains: list[dict]

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
        self.workflow.add_node("plan", self._plan_node)
        self.workflow.add_node("retrieve", self._retrieve_node)
        self.workflow.add_node("filter", self._filter_node)
        self.workflow.add_node("parse", self._parse_node)
        self.workflow.add_node("extract", self._extract_node)
        self.workflow.add_node("analyze", self._analyze_node)
        self.workflow.add_node("verify", self._verify_node)
        self.workflow.add_node("generate_report", self._report_node)

        # 设置入口点（任务规划为入口）
        self.workflow.set_entry_point("plan")

        # 添加边
        self.workflow.add_edge("plan", "retrieve")
        self.workflow.add_edge("retrieve", "filter")
        self.workflow.add_edge("filter", "parse")
        self.workflow.add_edge("parse", "extract")
        self.workflow.add_edge("extract", "analyze")
        self.workflow.add_edge("analyze", "verify")
        self.workflow.add_edge("verify", "generate_report")
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
    def _plan_node(self, state: WorkflowState) -> dict:
        """任务规划节点：分解研究问题并生成调研计划"""
        try:
            from litmat_agent.agents.planner_agent import (
                create_research_plan,
                decompose_task,
            )

            decompose_result = json.loads(
                decompose_task.invoke({"query": state["query"]})
            )
            plan_result = json.loads(
                create_research_plan.invoke({
                    "query": state["query"],
                    "max_results": state["max_results"],
                })
            )

            plan = {
                "query": state["query"],
                "detected_domains": decompose_result.get("detected_domains", []),
                "target_properties": decompose_result.get("target_properties", []),
                "search_queries": decompose_result.get("search_queries", []),
                "steps": plan_result.get("steps", []),
            }

            return {
                "plan": plan,
                "messages": [
                    (
                        "system",
                        f"任务规划完成：识别{len(plan['detected_domains'])}个领域，"
                        f"生成{len(plan['search_queries'])}个检索子问题",
                    )
                ],
            }
        except Exception as e:
            return {
                "plan": {
                    "query": state["query"],
                    "detected_domains": [],
                    "search_queries": [state["query"]],
                    "steps": [],
                },
                "messages": [("system", f"任务规划降级：{e}")],
            }

    def _retrieve_node(self, state: WorkflowState) -> dict:
        """文献检索节点：Sci-Base本地检索 + Sciverse实时API多源检索"""
        try:
            from litmat_agent.tools.sci_base import search_sci_base

            papers = []
            messages = []

            # 1) Sci-Base本地检索
            result = search_sci_base.invoke({
                "query": state["query"],
                "max_results": state["max_results"],
            })
            sci_base_result = json.loads(result)
            if isinstance(sci_base_result, dict) and "error" in sci_base_result:
                messages.append(f"Sci-Base检索降级：{sci_base_result['error']}")
            else:
                papers = sci_base_result
                messages.append(f"Sci-Base命中{len(papers)}篇")

            # 2) Sciverse补充/兜底（Sci-Base失败或结果不足时）
            if len(papers) < state["max_results"]:
                from litmat_agent.tools.sciverse import search_sciverse

                sciverse_result = json.loads(
                    search_sciverse.invoke({
                        "query": state["query"],
                        "max_results": state["max_results"] - len(papers),
                    })
                )
                sciverse_papers = sciverse_result.get("results", [])
                if sciverse_papers:
                    # 按标题去重合并
                    existing_titles = {
                        (p.get("title") or "").lower() for p in papers
                    }
                    for p in sciverse_papers:
                        if (p.get("title") or "").lower() not in existing_titles:
                            papers.append(p)
                            existing_titles.add((p.get("title") or "").lower())
                    messages.append(f"Sciverse补充{len(sciverse_papers)}篇")
                elif "error" in sciverse_result:
                    messages.append(f"Sciverse降级：{sciverse_result['error']}")

            return {
                "retrieved_papers": papers,
                "messages": [("system", "文献检索完成：" + "；".join(messages))],
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
            # 知识库存储（PostgreSQL + Neo4j，失败时优雅降级）
            store_note = self._store_knowledge_node(
                materials, properties, state["parsed_papers"]
            )

            return {
                "extracted_materials": materials,
                "extracted_properties": properties,
                "messages": [
                    (
                        "system",
                        f"知识抽取完成：{len(materials)}个材料，{len(properties)}条性能数据；{store_note}",
                    )
                ],
            }
        except Exception as e:
            return {
                "extracted_materials": [],
                "extracted_properties": [],
                "messages": [("system", f"知识抽取异常：{e}")],
            }

    def _store_knowledge_node(self, materials: list, properties: list, papers: list) -> str:
        """知识库存储：写入PostgreSQL + Neo4j（失败时优雅降级）

        Args:
            materials: 抽取的材料实体
            properties: 抽取的性能数据
            papers: 文献列表

        Returns:
            存储结果描述
        """
        try:
            from litmat_agent.core.database import (
                get_neo4j_manager,
                get_postgres_manager,
            )

            pg = get_postgres_manager()
            pg.create_tables()

            paper_id_map = {}
            for paper in papers:
                if not paper.get("title"):
                    continue
                try:
                    paper_id = pg.add_paper(paper)
                    paper_id_map[paper["title"]] = paper_id
                except Exception:
                    continue

            saved_materials = 0
            for m in materials:
                title = m.get("paper_title", "")
                paper_id = paper_id_map.get(title)
                if paper_id is None:
                    continue
                try:
                    pg.add_material(paper_id, {
                        "formula": m.get("formula", ""),
                        "material_type": m.get("material_type"),
                        "crystal_structure": m.get("crystal_structure"),
                    })
                    saved_materials += 1
                except Exception:
                    continue

            saved_properties = 0
            for p in properties:
                title = p.get("paper_title", "")
                paper_id = paper_id_map.get(title)
                if paper_id is None:
                    continue
                try:
                    pg.add_property(paper_id, {
                        "material_formula": p.get("material_formula"),
                        "property_name": p.get("property", ""),
                        "value": p.get("value", 0.0),
                        "unit": p.get("unit"),
                    })
                    saved_properties += 1
                except Exception:
                    continue

            # Neo4j图存储（可选，失败不影响主流程）
            graph_saved = False
            try:
                neo4j = get_neo4j_manager()
                neo4j.create_constraints()
                for paper in papers:
                    if paper.get("doi") and paper.get("title"):
                        neo4j.add_paper_node(paper)
                for m in materials[:50]:
                    formula = m.get("formula", "")
                    if formula:
                        neo4j.add_material_node(formula)
                graph_saved = True
            except Exception:
                graph_saved = False

            note = f"知识库存储完成：文献{len(paper_id_map)}篇，材料{saved_materials}条，性能{saved_properties}条"
            if graph_saved:
                note += "，图数据库已更新"
            return note
        except Exception as e:
            # 截断冗长的连接错误堆栈，仅保留首行
            err = str(e).split("\n")[0][:120]
            return f"知识库存储降级：{err}"

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

    def _verify_node(self, state: WorkflowState) -> dict:
        """证据核验节点：为每个Gap构建可审计证据链"""
        try:
            from litmat_agent.core.evidence import get_tracker

            tracker = get_tracker()
            chains = []

            for i, gap in enumerate(state["research_gaps"], 1):
                hypothesis_id = f"gap_{i}"
                prop_name = gap.get("property", "")

                # 找到支持该Gap的性能数据作为证据
                supporting = [
                    p for p in state["extracted_properties"]
                    if p.get("property") == prop_name
                ]
                for p in supporting:
                    quote = (
                        f"{p.get('paper_title', '文献')} 报道 {prop_name} = "
                        f"{p.get('value')} {p.get('unit', '')}"
                    )
                    tracker.add_evidence(
                        hypothesis_id=hypothesis_id,
                        paper_id=p.get("paper_title", "unknown"),
                        quote_text=quote,
                        confidence=0.8,
                    )

                chain = tracker.build_chain(hypothesis_id)
                chains.append({
                    "gap_index": i,
                    "hypothesis_id": hypothesis_id,
                    "property": prop_name,
                    "evidence_count": len(chain),
                    "evidence": chain,
                })

            # 各假设的证据链
            for i, hyp in enumerate(state["hypotheses"], 1):
                hypothesis_id = f"hyp_{i}"
                formula = hyp.get("formula", "")
                supporting = [
                    m for m in state["extracted_materials"]
                    if m.get("formula") == formula
                ]
                for m in supporting:
                    tracker.add_evidence(
                        hypothesis_id=hypothesis_id,
                        paper_id=m.get("paper_title", "unknown"),
                        quote_text=f"{m.get('paper_title', '文献')} 报道材料 {formula}",
                        confidence=0.6,
                    )
                chain = tracker.build_chain(hypothesis_id)
                chains.append({
                    "gap_index": None,
                    "hypothesis_id": hypothesis_id,
                    "property": formula,
                    "evidence_count": len(chain),
                    "evidence": chain,
                })

            return {
                "evidence_chains": chains,
                "messages": [
                    (
                        "system",
                        f"证据核验完成：{len(chains)}条证据链，"
                        f"共{sum(c['evidence_count'] for c in chains)}条证据",
                    )
                ],
            }
        except Exception as e:
            return {
                "evidence_chains": [],
                "messages": [("system", f"证据核验降级：{e}")],
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
                "evidence_chains": state.get("evidence_chains", []),
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
