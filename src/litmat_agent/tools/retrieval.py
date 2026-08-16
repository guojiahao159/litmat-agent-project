"""检索工具（兼容层：转发到已实现模块）

本模块保留原有函数名以兼容早期调用方，
实际功能由 hybrid_retrieval 模块提供。
"""

from litmat_agent.tools.hybrid_retrieval import (
    hybrid_search_advanced,
    rerank_documents,
)

# 向后兼容别名
hybrid_search = hybrid_search_advanced
rerank_results = rerank_documents
