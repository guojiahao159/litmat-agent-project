"""知识抽取模块：材料成分识别、性能数据抽取、单位统一"""

import json
import re
from typing import Optional

from langchain_core.tools import tool


class UnitConverter:
    """单位统一转换器"""

    # 电导率单位换算表（统一为 S/cm）
    CONDUCTIVITY_UNITS = {
        "s": 1.0,
        "ms": 1e-3,
        "µs": 1e-6,
        "us": 1e-6,
        "μs": 1e-6,
        "ns": 1e-9,
    }

    # 温度单位换算（统一为 K）
    TEMPERATURE_UNITS = {
        "k": lambda v: v,
        "°c": lambda v: v + 273.15,
        "c": lambda v: v + 273.15,
        "℃": lambda v: v + 273.15,
        "°f": lambda v: (v - 32) * 5 / 9 + 273.15,
        "f": lambda v: (v - 32) * 5 / 9 + 273.15,
    }

    # 长度单位换算（统一为 nm）
    LENGTH_UNITS = {
        "nm": 1.0,
        "µm": 1e3,
        "um": 1e3,
        "μm": 1e3,
        "mm": 1e6,
        "cm": 1e7,
        "m": 1e9,
        "å": 0.1,
        "a": 0.1,
    }

    @classmethod
    def convert_conductivity(cls, value: float, unit: str) -> float:
        """电导率单位统一为 S/cm

        Args:
            value: 数值
            unit: 原始单位（兼容 mS、mS/cm、mS·cm⁻¹ 等写法）

        Returns:
            统一后的数值（S/cm）
        """
        unit_lower = unit.lower().strip()
        # 剥离 "/cm" 后缀，容忍带或不带的写法
        for suffix in ("/cm", "·cm⁻¹", "scm-1", "s cm-1", "cm-1", "cm⁻¹"):
            unit_lower = unit_lower.replace(suffix, "")
        unit_lower = unit_lower.strip()
        if unit_lower in cls.CONDUCTIVITY_UNITS:
            return value * cls.CONDUCTIVITY_UNITS[unit_lower]
        return value

    @classmethod
    def convert_temperature(cls, value: float, unit: str) -> float:
        """温度单位统一为 K

        Args:
            value: 数值
            unit: 原始单位

        Returns:
            统一后的数值（K）
        """
        unit_lower = unit.lower().strip()
        if unit_lower in cls.TEMPERATURE_UNITS:
            return cls.TEMPERATURE_UNITS[unit_lower](value)
        return value

    @classmethod
    def convert_length(cls, value: float, unit: str) -> float:
        """长度单位统一为 nm

        Args:
            value: 数值
            unit: 原始单位

        Returns:
            统一后的数值（nm）
        """
        unit_lower = unit.lower().strip()
        if unit_lower in cls.LENGTH_UNITS:
            return value * cls.LENGTH_UNITS[unit_lower]
        return value


class MaterialExtractor:
    """材料信息抽取器"""

    # 常见固态电解质化学式模式
    MATERIAL_PATTERNS = [
        r"Li[0-9]*[A-Z][a-z]?[0-9]*(?:[A-Z][a-z]?[0-9]*)*",  # 锂化合物
        r"Na[0-9]*[A-Z][a-z]?[0-9]*(?:[A-Z][a-z]?[0-9]*)*",  # 钠化合物
        r"LLZO",  # 石榴石型
        r"LGPS",  # 硫化物
        r"Li[0-9]*La[0-9]*Zr[0-9]*O[0-9]*",  # LLZO详细式
        r"Li[0-9]*Ge[0-9]*P[0-9]*S[0-9]*",  # LGPS详细式
        r"PEO",  # 聚合物
        r"PVDF",  # 聚合物
        r"LiPON",  # 薄膜
    ]

    # 常见性能指标
    PROPERTY_PATTERNS = {
        "ionic_conductivity": r"(\d+(?:\.\d+)?)\s*(?:×\s*10[⁻¹⁰¹²³⁴⁵⁶⁷⁸⁹-]*\d*|e[-+]?\d+)?\s*(S|mS|µS|μS)\s*/\s*cm",
        "activation_energy": r"activation\s+energy[:\s]*(\d+(?:\.\d+)?)\s*(eV|kJ/mol)",
        "electrochemical_window": r"electrochemical\s+window[:\s]*(\d+(?:\.\d+)?)\s*(V)",
        "density": r"density[:\s]*(\d+(?:\.\d+)?)\s*(g/cm³|g/cm3)",
        "melting_point": r"melting\s+point[:\s]*(\d+(?:\.\d+)?)\s*(°C|℃|K)",
    }

    @classmethod
    def extract_materials(cls, text: str) -> list[dict]:
        """从文本中提取材料成分

        Args:
            text: 文献文本

        Returns:
            材料列表
        """
        materials = []
        seen = set()

        for pattern in cls.MATERIAL_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in seen:
                    seen.add(match)
                    materials.append({
                        "formula": match,
                        "count": text.count(match),
                    })

        return materials

    @classmethod
    def extract_properties(cls, text: str) -> list[dict]:
        """从文本中提取性能数据

        Args:
            text: 文献文本

        Returns:
            性能数据列表
        """
        properties = []

        for prop_name, pattern in cls.PROPERTY_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                unit = match.group(2) if match.lastindex >= 2 else ""

                # 单位统一
                if prop_name == "ionic_conductivity":
                    value = UnitConverter.convert_conductivity(value, unit)
                    unit = "S/cm"
                elif prop_name == "activation_energy":
                    unit = "eV"
                elif prop_name == "melting_point" and unit in ("°C", "℃"):
                    value = UnitConverter.convert_temperature(value, unit)
                    unit = "K"

                properties.append({
                    "property": prop_name,
                    "value": value,
                    "unit": unit,
                    "position": match.start(),
                })

        return properties

    @classmethod
    def extract_all(cls, text: str) -> dict:
        """抽取全部材料信息

        Args:
            text: 文献文本

        Returns:
            抽取结果
        """
        return {
            "materials": cls.extract_materials(text),
            "properties": cls.extract_properties(text),
        }


# 全局抽取器实例
_extractor = MaterialExtractor()


@tool
def extract_material_knowledge(paper_text: str) -> str:
    """从文献文本中抽取材料知识（成分、性能、单位统一）

    Args:
        paper_text: 文献全文或摘要文本

    Returns:
        抽取的知识JSON字符串
    """
    try:
        result = _extractor.extract_all(paper_text)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def normalize_units(value: float, unit: str, category: str) -> str:
    """统一单位换算

    Args:
        value: 数值
        unit: 原始单位
        category: 类别（conductivity/temperature/length）

    Returns:
        换算结果JSON
    """
    try:
        if category == "conductivity":
            result = UnitConverter.convert_conductivity(value, unit)
            target_unit = "S/cm"
        elif category == "temperature":
            result = UnitConverter.convert_temperature(value, unit)
            target_unit = "K"
        elif category == "length":
            result = UnitConverter.convert_length(value, unit)
            target_unit = "nm"
        else:
            return json.dumps({"error": f"未知类别: {category}"}, ensure_ascii=False)

        return json.dumps({
            "original": {"value": value, "unit": unit},
            "converted": {"value": result, "unit": target_unit},
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
