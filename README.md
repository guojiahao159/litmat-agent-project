# LitMat-Agent

面向固态电解质研发的文献驱动科学发现智能体系统

## 项目简介

LitMat-Agent 是一个基于 LangChain DeepAgent 构建的材料科学文献调研系统，专注于固态电解质领域的构效关系发现。系统通过多Agent协作，实现从科学问题输入到可验证构效关系假设输出的全流程自动化。

## 核心功能

- **5个专业化Agent**：文献调研、文献筛选、知识融合、研究分析、报告生成
- **多源文献检索**：Sci-Base本地库（Elasticsearch）+ Sciverse实时API
- **混合检索**：BGE-M3语义检索 + BM25关键词检索 + BGE-Reranker重排序
- **知识抽取**：材料成分识别、性能数据抽取、单位统一
- **知识融合**：跨文献实体对齐、性能数据冲突检测
- **证据链追踪**：引用链构建、原文定位
- **数据持久化**：PostgreSQL（ORM）+ Neo4j（知识图谱）

## 技术栈

- **Agent框架**：LangChain DeepAgent + LangGraph工作流编排
- **LLM支持**：OpenAI GPT-4 / Anthropic Claude
- **检索引擎**：Elasticsearch + sentence-transformers（BGE-M3/Reranker）
- **PDF解析**：MinerU
- **Web界面**：Streamlit
- **项目管理**：uv
- **版本控制**：git

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd litmat-agent-project

# 安装依赖
uv sync
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入API密钥
# OPENAI_API_KEY=your_key_here
# 或
# ANTHROPIC_API_KEY=your_key_here
```

### 3. 运行系统

```bash
# 启动主程序
uv run python main.py

# 启动Web交互界面
uv run streamlit run app.py
```

## 项目结构

```
litmat-agent-project/
├── src/litmat_agent/          # 源代码
│   ├── agents/                # Agent模块（5个）
│   │   ├── literature_agent.py   # 文献调研Agent
│   │   ├── filter_agent.py       # 文献筛选Agent
│   │   ├── fusion_agent.py       # 知识融合Agent
│   │   ├── research_agent.py     # 研究分析Agent
│   │   └── report_agent.py       # 报告生成Agent
│   ├── core/                  # 核心模块
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # PostgreSQL/Neo4j管理
│   │   ├── evidence.py           # 证据链追踪
│   │   └── workflow.py           # LangGraph工作流
│   ├── models/                # 数据模型
│   │   └── material.py           # 材料领域模型
│   └── tools/                 # 工具模块（7个）
│       ├── sci_base.py           # Sci-Base检索
│       ├── sciverse.py           # Sciverse API客户端
│       ├── hybrid_retrieval.py   # 混合检索
│       ├── pdf_parser.py         # MinerU PDF解析
│       ├── knowledge_extraction.py  # 知识抽取
│       ├── literature.py         # 文献处理工具
│       └── retrieval.py          # 检索工具
├── tests/                     # 测试代码
├── docs/                      # 文档
├── data/                      # 数据目录
├── app.py                     # Streamlit交互界面
├── main.py                    # 主入口
├── pyproject.toml             # 项目配置
└── .env.example               # 环境变量模板
```

## 开发计划

- [x] 实现Sci-Base本地文献检索
- [x] 集成Sciverse API
- [x] 实现MinerU PDF解析
- [ ] 构建材料知识图谱
- [x] 实现Research Gap自动识别
- [x] 开发Web交互界面

## 许可证

MIT License

## 联系方式

【待补充】
