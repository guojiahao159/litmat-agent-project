"""文献处理工具（兼容层：转发到已实现模块）

本模块保留原有函数名以兼容早期调用方，
实际功能由 sci_base / knowledge_extraction / pdf_parser 模块提供。
"""

from litmat_agent.tools.knowledge_extraction import extract_material_knowledge
from litmat_agent.tools.pdf_parser import parse_pdf_with_mineru
from litmat_agent.tools.sci_base import search_sci_base

# 向后兼容别名
search_literature = search_sci_base
extract_material_info = extract_material_knowledge
parse_pdf = parse_pdf_with_mineru
