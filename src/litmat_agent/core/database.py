"""数据库模块：PostgreSQL ORM + Neo4j图操作"""

import json
from datetime import datetime
from typing import Optional

from neo4j import GraphDatabase
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from litmat_agent.core.config import settings

Base = declarative_base()


# ========== PostgreSQL ORM模型 ==========


class Paper(Base):
    """文献表"""

    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    doi = Column(String(100), unique=True, index=True)
    authors = Column(JSON, default=list)
    journal = Column(String(200))
    year = Column(Integer, index=True)
    abstract = Column(Text)
    full_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaterialRecord(Base):
    """材料记录表"""

    __tablename__ = "material_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, index=True, nullable=False)
    formula = Column(String(200), nullable=False, index=True)
    material_type = Column(String(50), index=True)
    composition = Column(String(500))
    crystal_structure = Column(String(200))
    space_group = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class PropertyRecord(Base):
    """性能数据表"""

    __tablename__ = "property_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, index=True, nullable=False)
    material_formula = Column(String(200), index=True)
    property_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    condition = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class EvidenceRecord(Base):
    """证据链记录表"""

    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hypothesis_id = Column(String(100), index=True)
    paper_id = Column(Integer, index=True)
    quote_text = Column(Text)
    page_number = Column(Integer)
    paragraph_index = Column(Integer)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== PostgreSQL数据库管理器 ==========


class PostgresManager:
    """PostgreSQL数据库管理器"""

    def __init__(self, database_url: Optional[str] = None):
        """初始化数据库连接

        Args:
            database_url: 数据库连接URL，默认使用配置
        """
        self.database_url = database_url or settings.postgres_url
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False)

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    # ========== 文献操作 ==========

    def add_paper(self, paper_data: dict) -> int:
        """添加文献

        Args:
            paper_data: 文献数据

        Returns:
            文献ID
        """
        with self.get_session() as session:
            paper = Paper(
                title=paper_data.get("title", ""),
                doi=paper_data.get("doi"),
                authors=paper_data.get("authors", []),
                journal=paper_data.get("journal"),
                year=paper_data.get("year"),
                abstract=paper_data.get("abstract"),
                full_text=paper_data.get("full_text"),
            )
            session.add(paper)
            session.commit()
            session.refresh(paper)
            return paper.id

    def get_paper_by_doi(self, doi: str) -> Optional[dict]:
        """按DOI查询文献"""
        with self.get_session() as session:
            paper = session.query(Paper).filter(Paper.doi == doi).first()
            if paper:
                return {
                    "id": paper.id,
                    "title": paper.title,
                    "doi": paper.doi,
                    "authors": paper.authors,
                    "journal": paper.journal,
                    "year": paper.year,
                }
        return None

    def search_papers(self, keyword: str, limit: int = 10) -> list[dict]:
        """关键词搜索文献"""
        with self.get_session() as session:
            papers = (
                session.query(Paper)
                .filter(Paper.title.ilike(f"%{keyword}%"))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": p.id,
                    "title": p.title,
                    "doi": p.doi,
                    "year": p.year,
                }
                for p in papers
            ]

    # ========== 材料操作 ==========

    def add_material(self, paper_id: int, material_data: dict) -> int:
        """添加材料记录"""
        with self.get_session() as session:
            material = MaterialRecord(
                paper_id=paper_id,
                formula=material_data.get("formula", ""),
                material_type=material_data.get("material_type"),
                composition=material_data.get("composition"),
                crystal_structure=material_data.get("crystal_structure"),
                space_group=material_data.get("space_group"),
            )
            session.add(material)
            session.commit()
            session.refresh(material)
            return material.id

    def get_materials_by_paper(self, paper_id: int) -> list[dict]:
        """查询文献关联的材料"""
        with self.get_session() as session:
            materials = (
                session.query(MaterialRecord)
                .filter(MaterialRecord.paper_id == paper_id)
                .all()
            )
            return [
                {
                    "id": m.id,
                    "formula": m.formula,
                    "material_type": m.material_type,
                    "crystal_structure": m.crystal_structure,
                }
                for m in materials
            ]

    # ========== 性能数据操作 ==========

    def add_property(self, paper_id: int, property_data: dict) -> int:
        """添加性能数据"""
        with self.get_session() as session:
            prop = PropertyRecord(
                paper_id=paper_id,
                material_formula=property_data.get("material_formula"),
                property_name=property_data.get("property_name", ""),
                value=property_data.get("value", 0.0),
                unit=property_data.get("unit"),
                condition=property_data.get("condition"),
            )
            session.add(prop)
            session.commit()
            session.refresh(prop)
            return prop.id

    def get_properties_by_material(self, formula: str) -> list[dict]:
        """按材料查询性能数据"""
        with self.get_session() as session:
            props = (
                session.query(PropertyRecord)
                .filter(PropertyRecord.material_formula == formula)
                .all()
            )
            return [
                {
                    "id": p.id,
                    "property_name": p.property_name,
                    "value": p.value,
                    "unit": p.unit,
                    "condition": p.condition,
                }
                for p in props
            ]

    # ========== 证据操作 ==========

    def add_evidence(self, evidence_data: dict) -> int:
        """添加证据记录"""
        with self.get_session() as session:
            evidence = EvidenceRecord(
                hypothesis_id=evidence_data.get("hypothesis_id", ""),
                paper_id=evidence_data.get("paper_id", 0),
                quote_text=evidence_data.get("quote_text"),
                page_number=evidence_data.get("page_number"),
                paragraph_index=evidence_data.get("paragraph_index"),
                confidence=evidence_data.get("confidence", 0.0),
            )
            session.add(evidence)
            session.commit()
            session.refresh(evidence)
            return evidence.id

    def get_evidence_by_hypothesis(self, hypothesis_id: str) -> list[dict]:
        """按假设查询证据链"""
        with self.get_session() as session:
            evidences = (
                session.query(EvidenceRecord)
                .filter(EvidenceRecord.hypothesis_id == hypothesis_id)
                .all()
            )
            return [
                {
                    "id": e.id,
                    "paper_id": e.paper_id,
                    "quote_text": e.quote_text,
                    "page_number": e.page_number,
                    "confidence": e.confidence,
                }
                for e in evidences
            ]


# ========== Neo4j图数据库管理器 ==========


class Neo4jManager:
    """Neo4j图数据库管理器"""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """初始化Neo4j连接

        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
        """
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.driver = None

    def _get_driver(self):
        """获取Neo4j驱动"""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self.driver

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None

    def create_constraints(self):
        """创建图约束"""
        with self._get_driver().session() as session:
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Material) REQUIRE m.formula IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.doi IS UNIQUE"
            )

    # ========== 图操作 ==========

    def add_material_node(self, formula: str, properties: Optional[dict] = None):
        """添加材料节点"""
        props = properties or {}
        props["formula"] = formula
        with self._get_driver().session() as session:
            session.run(
                """
                MERGE (m:Material {formula: $formula})
                SET m += $properties
                """,
                formula=formula,
                properties=props,
            )

    def add_paper_node(self, paper_data: dict):
        """添加文献节点"""
        with self._get_driver().session() as session:
            session.run(
                """
                MERGE (p:Paper {doi: $doi})
                SET p.title = $title,
                    p.year = $year,
                    p.journal = $journal
                """,
                doi=paper_data.get("doi", ""),
                title=paper_data.get("title", ""),
                year=paper_data.get("year"),
                journal=paper_data.get("journal", ""),
            )

    def create_relation(
        self,
        source_formula: str,
        target_formula: str,
        relation_type: str,
        properties: Optional[dict] = None,
    ):
        """创建材料间关系

        Args:
            source_formula: 源材料化学式
            target_formula: 目标材料化学式
            relation_type: 关系类型（如 DOPED_WITH, SIMILAR_TO）
            properties: 关系属性
        """
        props = properties or {}
        # 动态关系类型需要转义
        relation_type = relation_type.upper().replace(" ", "_")
        with self._get_driver().session() as session:
            session.run(
                f"""
                MATCH (a:Material {{formula: $source}})
                MATCH (b:Material {{formula: $target}})
                MERGE (a)-[r:{relation_type}]->(b)
                SET r += $properties
                """,
                source=source_formula,
                target=target_formula,
                properties=props,
            )

    def link_paper_material(self, doi: str, formula: str, role: str = "STUDIES"):
        """关联文献与材料

        Args:
            doi: 文献DOI
            formula: 材料化学式
            role: 关系类型
        """
        role = role.upper().replace(" ", "_")
        with self._get_driver().session() as session:
            session.run(
                f"""
                MATCH (p:Paper {{doi: $doi}})
                MATCH (m:Material {{formula: $formula}})
                MERGE (p)-[r:{role}]->(m)
                """,
                doi=doi,
                formula=formula,
            )

    def query_material_relations(self, formula: str, depth: int = 2) -> list[dict]:
        """查询材料关系子图

        Args:
            formula: 材料化学式
            depth: 查询深度

        Returns:
            关系列表
        """
        with self._get_driver().session() as session:
            result = session.run(
                """
                MATCH path = (m:Material {formula: $formula})-[*1..$depth]-(related)
                RETURN m, related, relationships(path) as rels
                LIMIT 100
                """,
                formula=formula,
                depth=depth,
            )
            relations = []
            for record in result:
                for rel in record["rels"]:
                    relations.append({
                        "source": rel.start_node.get("formula"),
                        "target": rel.end_node.get("formula"),
                        "type": rel.type,
                    })
            return relations

    def query_papers_by_material(self, formula: str) -> list[dict]:
        """查询研究某材料的文献"""
        with self._get_driver().session() as session:
            result = session.run(
                """
                MATCH (p:Paper)-[:STUDIES]->(m:Material {formula: $formula})
                RETURN p.doi as doi, p.title as title, p.year as year
                """,
                formula=formula,
            )
            return [
                {"doi": r["doi"], "title": r["title"], "year": r["year"]}
                for r in result
            ]


# ========== 全局管理器实例 ==========

_postgres_manager: Optional[PostgresManager] = None
_neo4j_manager: Optional[Neo4jManager] = None


def get_postgres_manager() -> PostgresManager:
    """获取PostgreSQL管理器单例"""
    global _postgres_manager
    if _postgres_manager is None:
        _postgres_manager = PostgresManager()
    return _postgres_manager


def get_neo4j_manager() -> Neo4jManager:
    """获取Neo4j管理器单例"""
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jManager()
    return _neo4j_manager
