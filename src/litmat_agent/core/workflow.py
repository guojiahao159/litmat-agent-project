"""LangGraph工作流编排模块"""

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

    # 节点函数
    def _retrieve_node(self, state: WorkflowState) -> WorkflowState:
        """文献检索节点"""
        try:
            # TODO: 调用Sci-Base检索
            state["retrieved_papers"] = []
            state["messages"].append(("system", "文献检索完成"))
        except Exception as e:
            state["error"] = str(e)
        return state

    def _filter_node(self, state: WorkflowState) -> WorkflowState:
        """文献筛选节点"""
        try:
            # TODO: 实现筛选逻辑
            state["filtered_papers"] = state["retrieved_papers"]
            state["messages"].append(("system", "文献筛选完成"))
        except Exception as e:
            state["error"] = str(e)
        return state

    def _parse_node(self, state: WorkflowState) -> WorkflowState:
        """PDF解析节点"""
        try:
            # TODO: 调用MinerU解析
            state["parsed_papers"] = []
            state["messages"].append(("system", "PDF解析完成"))
        except Exception as e:
            state["error"] = str(e)
        return state

    def _extract_node(self, state: WorkflowState) -> WorkflowState:
        """知识抽取节点"""
        try:
            # TODO: 实现知识抽取
            state["extracted_materials"] = []
            state["extracted_properties"] = []
            state["messages"].append(("system", "知识抽取完成"))
        except Exception as e:
            state["error"] = str(e)
        return state

    def _analyze_node(self, state: WorkflowState) -> WorkflowState:
        """分析节点"""
        try:
            # TODO: 实现Gap分析和假设生成
            state["research_gaps"] = []
            state["hypotheses"] = []
            state["messages"].append(("system", "分析完成"))
        except Exception as e:
            state["error"] = str(e)
        return state

    def _report_node(self, state: WorkflowState) -> WorkflowState:
        """报告生成节点"""
        try:
            # TODO: 生成结构化报告
            state["report"] = "调研报告（待生成）"
            state["messages"].append(("system", "报告生成完成"))
        except Exception as e:
            state["error"] = str(e)
        return state

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
