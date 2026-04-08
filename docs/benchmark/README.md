# Benchmark 测试手册 - 小采 1.0 技术评测体系

**版本**: v1.0
**最后更新**: 2026-02-11
**维护者**: 技术团队
**目的**: 提供系统化、可复现的技术评测方法论

> 本目录是技术指标与模型表现控制中心；日常业务交付主线请从 `docs/discussions/contract-baseline/` 进入。

---

## 目录

1. [概述](#概述)
2. [测试环境](#测试环境)
3. [Benchmark 分类](#benchmark-分类)
4. [使用指南](#使用指南)
5. [数据采集与更新](#数据采集与更新)
6. [未来规划](#未来规划)

---

## 概述

### 为什么需要 Benchmark？

在 AI 原生应用开发中，技术选型直接影响：
- **性能**: 响应速度、吞吐量、资源消耗
- **成本**: Token 消耗、基础设施费用
- **质量**: 输出准确率、用户体验
- **可维护性**: 社区活跃度、文档完善度

本手册提供 **数据驱动** 的技术选型依据，避免主观判断和盲目跟风。

### 核心原则

1. **可复现性**: 所有测试提供完整代码和环境配置
2. **数据透明**: 原始数据可导出，引用来源可追溯
3. **持续更新**: 定期重测，跟踪技术演进
4. **实战导向**: 测试场景贴近真实业务需求

---

## 测试环境

### 标准测试环境（Phase 0）

| 组件 | 配置 | 版本 |
|------|------|------|
| 操作系统 | Ubuntu 22.04 LTS | - |
| CPU | Intel i7-12700 (12C20T) | - |
| 内存 | 32GB DDR4-3200 | - |
| 存储 | 1TB NVMe SSD | - |
| Python | 3.11.x | 3.11.7 |
| Docker | Docker Engine | 24.0.7 |
| GPU (可选) | NVIDIA RTX 4090 24GB | - |

### 网络环境

- 国内测试：中国电信 1000Mbps
- API 调用：通过代理（避免网络因素影响）
- 本地模型：Ollama 0.1.x

### 环境复现

```bash
# 克隆仓库
git clone https://github.com/your-org/procurement-agents.git
cd procurement-agents/docs/benchmark

# 安装依赖
pip install -r requirements.txt

# 验证环境
python scripts/verify_env.py
```

---

## Benchmark 分类

### 核心技术栈 Benchmark

| 编号 | 文档 | 测试对象 | 优先级 | 状态 |
|------|------|---------|--------|------|
| 01 | [LLM Benchmark](./01-llm-benchmark.md) | Claude / GPT-4 / Qwen | P0 | ✅ 完成 |
| 02 | [Knowledge Architecture Benchmark](./02-knowledge-architecture-benchmark.md) | Engram / RAG / GraphRAG | P0 | 🚧 进行中 |
| 03 | [Agent Framework Benchmark](./03-agent-framework-benchmark.md) | LangGraph / CrewAI / AutoGen | P1 | 📅 计划中 |
| 04 | [Vector Database Benchmark](./04-vector-database-benchmark.md) | Qdrant / Weaviate / Milvus | P1 | 📅 计划中 |
| 05 | [API Gateway Benchmark](./05-api-gateway-benchmark.md) | tRPC / GraphQL / REST | P2 | 📅 计划中 |
| 06 | [Frontend Framework Benchmark](./06-frontend-framework-benchmark.md) | Next.js / Remix / SvelteKit | P2 | 📅 计划中 |
| 07 | [End-to-End Benchmark](./07-end-to-end-benchmark.md) | 全链路性能测试 | P0 | 📅 计划中 |

### 辅助测试工具

| 工具 | 用途 | 路径 |
|------|------|------|
| Jupyter Notebooks | 交互式测试和可视化 | `notebooks/` |
| Python Scripts | 自动化批量测试 | `scripts/` |
| Test Data | 标准测试数据集 | `data/` |
| Reports/Research | 技术报告与研究沉淀 | `knowledge/` |

---

## 使用指南

### 快速开始

**场景 1: 选择 LLM 模型**

```bash
# 1. 阅读测试报告
cat docs/benchmark/01-llm-benchmark.md

# 2. 运行交互式测试
jupyter notebook notebooks/llm_comparison.ipynb

# 3. 自定义测试（可选）
python scripts/benchmark_llm.py \
  --models claude-sonnet-4.5,gpt-4-turbo,qwen-turbo \
  --scenario requirement_extraction \
  --iterations 100
```

**场景 2: 对比知识架构方案**

```bash
# 1. 阅读技术对比
cat docs/benchmark/02-knowledge-architecture-benchmark.md

# 2. 运行 RAG 测试
python scripts/benchmark_knowledge.py \
  --methods engram,graphrag,basic-rag \
  --dataset procurement_categories
```

**场景 3: 端到端性能测试**

```bash
# 启动本地环境
cd /Users/dantevonalcatraz/Development/procurement-agents
./start.sh

# 运行端到端测试
python docs/benchmark/scripts/benchmark_e2e.py \
  --api-url http://localhost:8001 \
  --scenarios requirement_chat,intelligent_sourcing \
  --concurrent-users 10
```

### 自定义测试

#### 1. 修改测试参数

编辑 `scripts/config.yaml`:

```yaml
llm_benchmark:
  models:
    - claude-sonnet-4.5
    - gpt-4-turbo
    - qwen-turbo
  scenarios:
    - requirement_extraction
    - supplier_matching
    - conversational_qa
  iterations: 100
  timeout: 30s

knowledge_benchmark:
  methods:
    - engram
    - graphrag
    - basic_rag
  datasets:
    - procurement_categories
    - supplier_knowledge
  metrics:
    - retrieval_precision
    - answer_relevance
    - latency
```

#### 2. 添加新测试场景

```python
# scripts/custom_scenario.py
from benchmark_framework import BenchmarkRunner, Scenario

class MyCustomScenario(Scenario):
    def __init__(self):
        super().__init__(name="custom_test")

    def setup(self):
        # 准备测试数据
        pass

    def run(self, model):
        # 执行测试
        pass

    def teardown(self):
        # 清理资源
        pass

# 运行
runner = BenchmarkRunner()
runner.add_scenario(MyCustomScenario())
runner.execute()
```

---

## 数据采集与更新

### 更新频率

| 数据类型 | 更新频率 | 负责人 | 触发条件 |
|---------|---------|--------|---------|
| LLM 性能数据 | 每月 | AI 团队 | 新模型发布 |
| 开源框架对比 | 每季度 | 架构师 | 版本更新 |
| 端到端性能 | 每周 | DevOps | 代码变更 |
| 成本数据 | 每月 | 财务/技术 | 价格调整 |

### 数据来源

1. **自测数据**: 本地环境测试
2. **开源社区**: GitHub Trending, Papers with Code
3. **学术论文**: arXiv, ACL, NeurIPS
4. **行业报告**: Gartner, Forrester (如可获取)
5. **竞品分析**: 公开技术博客、开源实现

### 数据存储

```
docs/benchmark/
├── data/
│   ├── llm_performance_2026-02.csv
│   ├── knowledge_retrieval_2026-02.csv
│   └── e2e_latency_2026-02-11.csv
├── reports/
│   ├── 2026-02-11-llm-comparison.pdf
│   └── 2026-02-11-weekly-performance.md
└── archives/
    └── 2026-01/
        └── historical_data.csv
```

---

## 未来规划

### Phase 1: 自动化监控（Q2 2026）

**目标**: 构建 "daily tech inspection" 工具

**功能**:
- 自动抓取 GitHub Trending (AI/ML 分类)
- RSS 订阅 arXiv cs.AI / cs.CL
- 每日生成技术动态摘要
- 关键技术指标变化告警

**技术栈**:
- GitHub Actions (定时任务)
- Python (数据采集)
- Markdown (报告生成)
- Email/Slack (推送)

### Phase 2: 智能分析（Q3 2026）

**目标**: AI 驱动的技术选型建议

**功能**:
- 基于历史数据训练决策模型
- 自动生成 Johnny Wick 5 维度报告
- 技术债预警
- 性能回归检测

### Phase 3: 社区共建（Q4 2026）

**目标**: 开源 Benchmark 数据集

**内容**:
- 公开测试数据和代码
- 接受社区贡献
- 发布年度技术报告
- 举办技术选型研讨会

---

## 常见问题

### Q: Benchmark 数据是否适用于我的场景？

A: 本手册基于 **小采 1.0 MVP** 场景设计（采购需求梳理 + 智能寻源）。如果你的场景差异较大，建议：
- 调整测试参数（如并发数、数据规模）
- 增加领域特定测试
- 参考方法论自行测试

### Q: 如何确保测试结果的可靠性？

A: 我们采用以下措施：
- **统计显著性检验**: t-test, p < 0.05
- **多次重复测试**: n >= 30
- **控制变量**: 固定环境、数据集、Prompt
- **数据公开**: 原始数据可下载验证

### Q: 如何贡献 Benchmark 数据？

A: 欢迎通过以下方式参与：
1. 提交 Issue: 报告测试结果差异
2. 提交 PR: 新增测试场景或数据
3. 讨论区: 分享经验和见解

---

## 参考资料

### 核心资料

1. **项目架构文档**: [03-technical-architecture.md](../03-technical-architecture.md)
2. **技术选型报告**: [reports/tech-selection/](../reports/tech-selection/)
3. **开源参考项目**: [OPEN-SOURCE-REFERENCES.md](../OPEN-SOURCE-REFERENCES.md)

### 学术论文

1. RouteLLM (Berkeley/LMSYS) - arXiv:2406.18665
2. Engram: Knowledge Graphs Meet LLMs - arXiv:2312.xxxx
3. GraphRAG: Unlocking LLM discovery on narrative private data - Microsoft Research

### 工具和框架

1. LangChain Benchmarks - https://github.com/langchain-ai/langchain-benchmarks
2. HELM (Stanford) - https://crfm.stanford.edu/helm/
3. OpenAI Evals - https://github.com/openai/evals

---

## 文档变更日志

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2026-02-11 | v1.0 | 初始版本，完成框架设计 | Tech Team |

---

**文档状态**: ✅ 活跃维护
**许可证**: MIT License
**联系方式**: tech@xiaocai.com
