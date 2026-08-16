"""证据链追踪模块：引用链构建与原文定位"""

import json
import re
from typing import Optional

from langchain_core.tools import tool


class EvidenceTracker:
    """证据链追踪器"""

    def __init__(self):
        """初始化证据链追踪器"""
        self.evidence_chains: dict[str, list[dict]] = {}

    def add_evidence(
        self,
        hypothesis_id: str,
        paper_id: str,
        quote_text: str,
        page_number: Optional[int] = None,
        paragraph_index: Optional[int] = None,
        confidence: float = 0.0,
    ):
        """添加证据记录

        Args:
            hypothesis_id: 假设ID
            paper_id: 文献ID
            quote_text: 引用原文
            page_number: 页码
            paragraph_index: 段落索引
            confidence: 置信度
        """
        evidence = {
            "hypothesis_id": hypothesis_id,
            "paper_id": paper_id,
            "quote_text": quote_text,
            "page_number": page_number,
            "paragraph_index": paragraph_index,
            "confidence": confidence,
        }

        if hypothesis_id not in self.evidence_chains:
            self.evidence_chains[hypothesis_id] = []

        self.evidence_chains[hypothesis_id].append(evidence)

    def build_chain(self, hypothesis_id: str) -> list[dict]:
        """构建证据链

        Args:
            hypothesis_id: 假设ID

        Returns:
            按置信度排序的证据列表
        """
        chain = self.evidence_chains.get(hypothesis_id, [])
        return sorted(chain, key=lambda x: x["confidence"], reverse=True)

    def locate_quote(self, full_text: str, quote_text: str) -> Optional[dict]:
        """在原文中定位引用片段

        Args:
            full_text: 文献全文
            quote_text: 引用片段

        Returns:
            定位结果（页码、段落索引、上下文）
        """
        # 按段落分割
        paragraphs = full_text.split("\n\n")

        for idx, paragraph in enumerate(paragraphs):
            # 查找引用片段
            if quote_text in paragraph:
                # 计算大概页码（假设每页50行）
                page_number = (idx // 50) + 1
                return {
                    "paragraph_index": idx,
                    "page_number": page_number,
                    "context": paragraph[:500],  # 前500字符作为上下文
                }

        return None

    def verify_evidence(
        self,
        hypothesis_id: str,
        full_text: str,
        paper_id: str,
    ) -> dict:
        """验证证据链完整性

        Args:
            hypothesis_id: 假设ID
            full_text: 文献全文
            paper_id: 文献ID

        Returns:
            验证结果
        """
        chain = self.build_chain(hypothesis_id)
        verification = {
            "hypothesis_id": hypothesis_id,
            "total_evidence": len(chain),
            "verified_evidence": [],
            "unverified_evidence": [],
        }

        for evidence in chain:
            if evidence["paper_id"] == paper_id:
                location = self.locate_quote(full_text, evidence["quote_text"])
                if location:
                    evidence.update(location)
                    evidence["verified"] = True
                    verification["verified_evidence"].append(evidence)
                else:
                    evidence["verified"] = False
                    verification["unverified_evidence"].append(evidence)

        verification["verification_rate"] = (
            len(verification["verified_evidence"]) / len(chain) if chain else 0.0
        )

        return verification


class CitationParser:
    """引用解析器"""

    @staticmethod
    def extract_citations(text: str) -> list[dict]:
        """从文本中提取引用

        Args:
            text: 文献文本

        Returns:
            引用列表
        """
        citations = []

        # 匹配 [1], [2,3], [4-6] 等引用格式
        bracket_pattern = r"\[(\d+(?:\s*[,，\-–]\s*\d+)*)\]"
        matches = re.findall(bracket_pattern, text)

        for match in matches:
            # 解析引用编号
            numbers = re.split(r"[,，\-–]", match)
            for num in numbers:
                num = num.strip()
                if num.isdigit():
                    citations.append({
                        "type": "bracket",
                        "number": int(num),
                        "raw": f"[{match}]",
                    })

        return citations

    @staticmethod
    def build_citation_chain(text: str, reference_list: list[str]) -> list[dict]:
        """构建引用链

        Args:
            text: 正文文本
            reference_list: 参考文献列表

        Returns:
            引用链
        """
        citations = CitationParser.extract_citations(text)
        chain = []

        for citation in citations:
            num = citation["number"]
            if 1 <= num <= len(reference_list):
                chain.append({
                    "number": num,
                    "reference": reference_list[num - 1],
                    "position": citation["raw"],
                })

        return chain


# 全局追踪器实例
_tracker: Optional[EvidenceTracker] = None


def get_tracker() -> EvidenceTracker:
    """获取证据链追踪器单例"""
    global _tracker
    if _tracker is None:
        _tracker = EvidenceTracker()
    return _tracker


@tool
def add_evidence_record(
    hypothesis_id: str,
    paper_id: str,
    quote_text: str,
    page_number: Optional[int] = None,
    paragraph_index: Optional[int] = None,
    confidence: float = 0.0,
) -> str:
    """添加证据链记录

    Args:
        hypothesis_id: 假设ID
        paper_id: 文献ID
        quote_text: 引用原文
        page_number: 页码
        paragraph_index: 段落索引
        confidence: 置信度（0-1）

    Returns:
        操作结果
    """
    try:
        tracker = get_tracker()
        tracker.add_evidence(
            hypothesis_id=hypothesis_id,
            paper_id=paper_id,
            quote_text=quote_text,
            page_number=page_number,
            paragraph_index=paragraph_index,
            confidence=confidence,
        )
        return json.dumps({"success": True}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def build_evidence_chain(hypothesis_id: str) -> str:
    """构建假设的证据链

    Args:
        hypothesis_id: 假设ID

    Returns:
        证据链JSON
    """
    try:
        tracker = get_tracker()
        chain = tracker.build_chain(hypothesis_id)
        return json.dumps(chain, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def locate_quote_in_text(full_text: str, quote_text: str) -> str:
    """在原文中定位引用片段

    Args:
        full_text: 文献全文
        quote_text: 引用片段

    Returns:
        定位结果JSON
    """
    try:
        tracker = get_tracker()
        result = tracker.locate_quote(full_text, quote_text)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def verify_evidence_chain(hypothesis_id: str, full_text: str, paper_id: str) -> str:
    """验证证据链完整性

    Args:
        hypothesis_id: 假设ID
        full_text: 文献全文
        paper_id: 文献ID

    Returns:
        验证结果JSON
    """
    try:
        tracker = get_tracker()
        result = tracker.verify_evidence(hypothesis_id, full_text, paper_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def extract_citation_chain(text: str, reference_list_json: str) -> str:
    """构建引用链

    Args:
        text: 正文文本
        reference_list_json: 参考文献列表JSON

    Returns:
        引用链JSON
    """
    try:
        reference_list = json.loads(reference_list_json)
        chain = CitationParser.build_citation_chain(text, reference_list)
        return json.dumps(chain, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
