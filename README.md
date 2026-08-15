# LitMat-Agent

面向固态电解质研发的文献驱动科学发现智能体系统

## 项目简介

LitMat-Agent 是一个基于 LangChain DeepAgent 构建的材料科学文献调研系统，专注于固态电解质领域的构效关系发现。系统通过多Agent协作，实现从科学问题输入到可验证构效关系假设输出的全流程自动化。

## 核心功能

- **文献调研Agent**：检索、筛选、解析材料科学文献
- **研究分析Agent**：识别Research Gap、生成可验证假设
- **知识抽取**：从文献中抽取材料成分、结构、性能信息
- **混合检索**：结合语义检索和关键词检索

## 技术栈

- **Agent框架**：LangChain DeepAgent
- **LLM支持**：OpenAI GPT-4 / Anthropic Claude
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
```

## 项目结构

```
litmat-agent-project/
├── src/litmat_agent/          # 源代码
│   ├── agents/                # Agent模块
│   │   ├── literature_agent.py   # 文献调研Agent
│   │   └── research_agent.py     # 研究分析Agent
│   ├── core/                  # 核心模块
│   │   └── config.py             # 配置管理
│   ├── models/                # 数据模型
│   │   └── material.py           # 材料领域模型
│   └── tools/                 # 工具模块
│       ├── literature.py         # 文献处理工具
│       └── retrieval.py          # 检索工具
├── tests/                     # 测试代码
├── docs/                      # 文档
├── data/                      # 数据目录
├── main.py                    # 主入口
├── pyproject.toml             # 项目配置
└── .env.example               # 环境变量模板
```

## 开发计划

- [ ] 实现Sci-Base本地文献检索
- [ ] 集成Sciverse API
- [ ] 实现MinerU PDF解析
- [ ] 构建材料知识图谱
- [ ] 实现Research Gap自动识别
- [ ] 开发Web交互界面

## 许可证

MIT License

## 联系方式

【待补充】
