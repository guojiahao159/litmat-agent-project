"""材料领域数据模型"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MaterialType(str, Enum):
    """材料类型"""

    SULFIDE = "sulfide"  # 硫化物
    OXIDE = "oxide"  # 氧化物
    POLYMER = "polymer"  # 聚合物
    COMPOSITE = "composite"  # 复合电解质
    OTHER = "other"


class MaterialEntity(BaseModel):
    """材料实体"""

    name: str = Field(..., description="材料名称或化学式")
    material_type: MaterialType = Field(default=MaterialType.OTHER, description="材料类型")
    composition: Optional[str] = Field(default=None, description="化学成分")
    crystal_structure: Optional[str] = Field(default=None, description="晶体结构")
    space_group: Optional[str] = Field(default=None, description="空间群")


class MaterialProperty(BaseModel):
    """材料性能"""

    material_name: str = Field(..., description="关联的材料名称")
    property_name: str = Field(..., description="性能名称")
    value: Optional[float] = Field(default=None, description="性能数值")
    unit: Optional[str] = Field(default=None, description="单位")
    condition: Optional[str] = Field(default=None, description="测试条件")
    source_paper: Optional[str] = Field(default=None, description="来源文献")


class ResearchGap(BaseModel):
    """研究空白"""

    title: str = Field(..., description="Gap标题")
    description: str = Field(..., description="详细描述")
    gap_type: str = Field(..., description="Gap类型：矛盾/缺失/未探索")
    supporting_papers: list[str] = Field(default_factory=list, description="支撑文献")
    novelty_score: float = Field(default=0.0, ge=0, le=5, description="新颖性评分")
    feasibility_score: float = Field(default=0.0, ge=0, le=5, description="可行性评分")
    evidence_chain: list[str] = Field(default_factory=list, description="证据链")
    hypothesis: Optional[str] = Field(default=None, description="可证伪假设")
    validation_method: Optional[str] = Field(default=None, description="建议验证方法")
