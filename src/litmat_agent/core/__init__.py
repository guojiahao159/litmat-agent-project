"""核心模块：配置、模型、常量"""

from .config import settings
from .database import (
    PostgresManager,
    Neo4jManager,
    get_postgres_manager,
    get_neo4j_manager,
)
from .evidence import (
    EvidenceTracker,
    CitationParser,
    get_tracker,
    add_evidence_record,
    build_evidence_chain,
    locate_quote_in_text,
    verify_evidence_chain,
    extract_citation_chain,
)
from .workflow import LiteratureWorkflow, create_workflow

__all__ = [
    "settings",
    "LiteratureWorkflow",
    "create_workflow",
    "PostgresManager",
    "Neo4jManager",
    "get_postgres_manager",
    "get_neo4j_manager",
    "EvidenceTracker",
    "CitationParser",
    "get_tracker",
    "add_evidence_record",
    "build_evidence_chain",
    "locate_quote_in_text",
    "verify_evidence_chain",
    "extract_citation_chain",
]
