"""MinerU PDF解析模块"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool


class MinerUParser:
    """MinerU PDF解析器"""

    def __init__(self, mineru_path: Optional[str] = None):
        """初始化MinerU解析器

        Args:
            mineru_path: MinerU可执行文件路径，None则使用系统PATH
        """
        self.mineru_path = mineru_path or "mineru"
        self._check_installation()

    def _check_installation(self) -> bool:
        """检查MinerU是否安装"""
        try:
            result = subprocess.run(
                [self.mineru_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def parse_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        extract_images: bool = False,
    ) -> dict:
        """解析PDF文件

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录，None则使用临时目录
            extract_images: 是否提取图片

        Returns:
            解析结果字典
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {"error": f"文件不存在: {pdf_path}"}

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="mineru_")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # 构建MinerU命令
            cmd = [
                self.mineru_path,
                "-p",
                str(pdf_file),
                "-o",
                str(output_path),
            ]

            if extract_images:
                cmd.append("--images")

            # 执行解析
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            if result.returncode != 0:
                return {
                    "error": f"MinerU解析失败: {result.stderr}",
                    "pdf_path": pdf_path,
                }

            # 读取解析结果
            return self._read_output(output_path, pdf_file.stem)

        except subprocess.TimeoutExpired:
            return {"error": "解析超时", "pdf_path": pdf_path}
        except Exception as e:
            return {"error": str(e), "pdf_path": pdf_path}

    def _read_output(self, output_dir: Path, pdf_name: str) -> dict:
        """读取MinerU输出结果

        Args:
            output_dir: 输出目录
            pdf_name: PDF文件名（不含扩展名）

        Returns:
            解析结果
        """
        result = {
            "pdf_name": pdf_name,
            "text": "",
            "metadata": {},
            "tables": [],
            "figures": [],
        }

        # 查找输出文件
        md_file = output_dir / f"{pdf_name}.md"
        json_file = output_dir / f"{pdf_name}.json"

        # 读取Markdown文本
        if md_file.exists():
            result["text"] = md_file.read_text(encoding="utf-8")

        # 读取JSON元数据
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    result["metadata"] = metadata
            except Exception:
                pass

        return result


# 全局解析器实例
_parser: Optional[MinerUParser] = None


def get_parser() -> MinerUParser:
    """获取MinerU解析器单例"""
    global _parser
    if _parser is None:
        _parser = MinerUParser()
    return _parser


@tool
def parse_pdf_with_mineru(pdf_path: str, extract_images: bool = False) -> str:
    """使用MinerU解析PDF文献

    Args:
        pdf_path: PDF文件路径
        extract_images: 是否提取图片

    Returns:
        解析结果JSON字符串
    """
    try:
        parser = get_parser()
        result = parser.parse_pdf(pdf_path, extract_images=extract_images)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF中提取纯文本

    Args:
        pdf_path: PDF文件路径

    Returns:
        提取的文本内容
    """
    try:
        parser = get_parser()
        result = parser.parse_pdf(pdf_path)
        if "error" in result:
            return f"解析错误: {result['error']}"
        return result.get("text", "")
    except Exception as e:
        return f"提取失败: {str(e)}"
