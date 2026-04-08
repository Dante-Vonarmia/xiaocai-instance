# Knowledge Architecture Benchmark - 知识架构对比测试

**测试编号**: BM-KA-2026-02-11
**测试版本**: v1.0 (大纲)
**测试日期**: TBD
**负责人**: AI Team
**状态**: 🚧 规划中

---

## 目录

1. [测试目标](#测试目标)
2. [候选方案](#候选方案)
3. [测试方法](#测试方法)
4. [测试指标](#测试指标)
5. [预期结果](#预期结果)
6. [实施计划](#实施计划)

---

## 1. 测试目标

### 1.1 核心问题

在小采 1.0 MVP 场景下，选择哪种知识架构能够：
1. **检索准确率最高**: 相关文档召回率 > 90%
2. **推理能力最强**: 能理解隐含关系、跨品类推荐
3. **冷启动最快**: 从 0 到可用 < 1 周
4. **成本最低**: 构建成本 + 维护成本 + 查询成本

### 1.2 候选方案

| 方案 | 核心技术 | 代表项目 | 优势 | 劣势 |
|------|---------|---------|------|------|
| **Basic RAG** | Vector Search | LlamaIndex | 实现简单，成熟 | 无推理能力 |
| **GraphRAG** | Graph + Vector | Microsoft GraphRAG | 关系推理强 | 构建复杂 |
| **Engram** | Graph + LLM | Engram (NYU) | 动态学习 | 新技术，风险高 |
| **Hybrid** | 多策略融合 | 自研 | 灵活 | 维护成本高 |

---

## 2. 候选方案详解

### 2.1 Basic RAG (Retrieval-Augmented Generation)

**架构**:
```
用户查询 → Embedding → Vector Search (Top-K) → LLM 生成答案
```

**技术栈**:
- Embedding: OpenAI text-embedding-3, sentence-transformers
- Vector DB: Qdrant, ChromaDB, Pinecone
- LLM: Claude Sonnet 4.5

**优势**:
- 实现简单，1-2 天可上线
- 社区成熟，大量开源案例
- 成本低（仅 Embedding + Vector Search）

**劣势**:
- 无法理解实体关系（如"办公电脑"和"显示器"常搭配）
- 无法跨品类推荐
- 依赖查询表述（换个说法可能查不到）

**适用场景**:
- 文档问答
- FAQ 系统
- 语义搜索

---

### 2.2 GraphRAG (Knowledge Graph + RAG)

**架构**:
```
用户查询 → 意图识别 → 知识图谱查询 (Cypher/SPARQL) + Vector Search → LLM 生成答案
```

**技术栈**:
- Graph DB: Neo4j, NetworkX
- Vector DB: Qdrant
- Knowledge Extraction: GPT-4, spaCy
- LLM: Claude Sonnet 4.5

**优势**:
- 理解实体关系（"办公电脑" → "显示器" → "鼠标键盘"）
- 支持多跳推理（"需要会议室设备" → "投影仪" + "会议麦克风" + "视频会议系统"）
- 可解释性强（展示推理路径）

**劣势**:
- 构建成本高（知识抽取 + 关系标注）
- 维护成本高（知识图谱更新）
- 查询复杂（需要 Cypher/SPARQL）

**适用场景**:
- 复杂需求推理
- 跨品类推荐
- 供应商关系网络

**参考实现**:
- Microsoft GraphRAG - https://github.com/microsoft/graphrag
- LlamaIndex Knowledge Graph - https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/

---

### 2.3 Engram (LLM + Memory Graph)

**架构**:
```
用户查询 → LLM 生成子查询 → 多次检索 + 推理 → 更新知识图谱 → 生成答案
```

**核心思想**:
- LLM 作为"大脑"，知识图谱作为"长期记忆"
- 每次对话后自动更新知识图谱
- 动态学习用户偏好和领域知识

**技术栈**:
- 论文: "Engram: Knowledge Graphs Meet LLMs" (NYU, arXiv:2312.xxxx)
- 实现: 需自研（无成熟开源实现）

**优势**:
- 自动学习，无需人工标注
- 适应性强（随使用逐步优化）
- 理论上性能最优

**劣势**:
- 技术风险高（新论文，未经生产验证）
- 实现复杂（需 3-4 周开发）
- 依赖 LLM 质量（错误推理会污染知识图谱）

**适用场景**:
- Phase 1-2 探索
- 需要持续学习的场景

---

### 2.4 Hybrid (混合方案)

**架构**:
```
用户查询 → 意图分类 →
  - 简单查询 → Basic RAG
  - 复杂推理 → GraphRAG
  - 开放问答 → 纯 LLM
```

**优势**:
- 灵活，根据场景选择最优策略
- 成本可控（简单查询不走复杂流程）

**劣势**:
- 维护成本高（多套系统）
- 路由策略复杂

---

## 3. 测试方法

### 3.1 测试数据集

**来源**: 小采 1.0 采购需求真实数据（脱敏）

| 数据集 | 数量 | 描述 | 难度 |
|--------|------|------|------|
| 简单品类查询 | 50 | "办公电脑品类有哪些？" | ⭐ |
| 关系推理 | 30 | "采购会议室设备需要哪些配套？" | ⭐⭐⭐ |
| 供应商推荐 | 30 | "北京有哪些优质办公家具供应商？" | ⭐⭐⭐ |
| 跨品类组合 | 20 | "新办公楼装修需要哪些采购？" | ⭐⭐⭐⭐ |

### 3.2 测试场景

#### 场景 1: 检索准确率测试

**任务**: 给定查询，检索相关文档

**评分标准**:
- 召回率 (Recall@K): 前 K 个结果中相关文档占比
- 精确率 (Precision@K): 前 K 个结果中相关文档的准确率
- NDCG@K: 归一化折损累积增益

#### 场景 2: 关系推理测试

**任务**: 推荐配套品类

**示例**:
```
输入: "需要采购会议室设备"
期望输出:
- 投影仪/大屏显示器
- 会议麦克风
- 视频会议摄像头
- 会议桌椅
- 白板/电子白板
```

**评分标准**:
- 推荐完整性 (Coverage)
- 推荐合理性 (Relevance)
- 推荐排序 (Ranking Quality)

#### 场景 3: 冷启动测试

**任务**: 从 0 构建知识库到可用

**评分标准**:
- 构建时间
- 所需数据量
- 人工标注工作量

---

## 4. 测试指标

### 4.1 性能指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| 召回率@10 | 前 10 个结果中相关文档占比 | > 90% |
| 精确率@10 | 前 10 个结果的准确率 | > 70% |
| NDCG@10 | 考虑排序的综合指标 | > 0.8 |
| 查询延迟 | 单次查询平均时间 | < 500ms |

### 4.2 成本指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| 构建成本 | 知识库初始化时间 + LLM 调用费用 | < $100 |
| 维护成本/月 | 知识更新 + 质量保障 | < $50 |
| 查询成本 | 单次查询费用（LLM + DB） | < $0.01 |

### 4.3 易用性指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| 冷启动时间 | 从 0 到可用 | < 1 周 |
| 知识更新周期 | 新增数据到生效 | < 1 天 |
| 人工标注量 | 所需标注数据量 | < 100 条 |

---

## 5. 预期结果（假设）

**基于开源 Benchmark 和专家经验**:

| 方案 | 召回率@10 | 精确率@10 | NDCG@10 | 查询延迟 | 构建成本 | 综合评分 |
|------|----------|----------|---------|---------|---------|---------|
| Basic RAG | 85% | 75% | 0.78 | 200ms | $20 | 80/100 |
| GraphRAG | 92% | 82% | 0.85 | 350ms | $500 | 88/100 |
| Engram | 95% | 88% | 0.89 | 450ms | $1000+ | 92/100 (理论) |
| Hybrid | 90% | 80% | 0.83 | 250ms | $300 | 86/100 |

**推荐方案**:
- **Phase 0**: Basic RAG（快速上线，成本低）
- **Phase 1**: GraphRAG（提升质量，支持复杂推理）
- **Phase 2**: Engram（探索前沿，持续优化）

---

## 6. 实施计划

### 6.1 Phase 0 (当前)

**任务**: 实现 Basic RAG

**时间**: 1 周

**步骤**:
1. 准备测试数据集（采购品类文档、FAQ）
2. 选择 Embedding 模型（OpenAI text-embedding-3）
3. 选择 Vector DB（Qdrant）
4. 实现检索 + 生成流程
5. 运行 Benchmark 测试

**交付物**:
- 可运行的 RAG 系统
- Benchmark 测试报告

---

### 6.2 Phase 1 (Q2 2026)

**任务**: 实现 GraphRAG

**时间**: 3-4 周

**步骤**:
1. 知识抽取（使用 GPT-4 从文档中提取实体和关系）
2. 构建知识图谱（Neo4j 或 NetworkX）
3. 实现混合检索（Graph + Vector）
4. 对比 Benchmark（vs Basic RAG）
5. 优化查询性能

**交付物**:
- 采购品类知识图谱
- GraphRAG 系统
- 对比 Benchmark 报告

---

### 6.3 Phase 2 (Q3-Q4 2026)

**任务**: 探索 Engram 或自研方案

**时间**: 6-8 周

**步骤**:
1. 研究 Engram 论文和开源实现
2. 设计动态学习机制
3. 实现原型系统
4. 长期运行测试（收集真实用户数据）
5. 评估效果和成本

**交付物**:
- Engram 原型
- 长期性能报告
- 技术选型最终建议

---

## 7. 参考资料

### 7.1 学术论文

1. **GraphRAG: Unlocking LLM discovery on narrative private data**
   - 作者: Microsoft Research
   - 链接: https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/

2. **Engram: Knowledge Graphs Meet LLMs**
   - 作者: NYU
   - arXiv: TBD (论文尚未正式发布，需核实)

3. **Self-RAG: Learning to Retrieve, Generate, and Critique**
   - 作者: University of Washington
   - arXiv: 2310.11511

### 7.2 开源实现

1. **Microsoft GraphRAG** - https://github.com/microsoft/graphrag
2. **LlamaIndex** - https://github.com/run-llama/llama_index
3. **LangChain** - https://github.com/langchain-ai/langchain
4. **Neo4j LLM Knowledge Graph** - https://github.com/neo4j-labs/llm-graph-builder

### 7.3 Benchmark 数据集

1. **MS MARCO** - 微软问答数据集
2. **Natural Questions** - Google 自然问答
3. **HotpotQA** - 多跳推理问答

---

**文档状态**: 🚧 大纲完成，待实施
**预计完成时间**: Phase 0 (2026-02-20), Phase 1 (2026-04-30)
**联系方式**: ai-team@xiaocai.com
