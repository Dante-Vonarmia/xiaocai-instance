# 小采 AI 助手 1.0 企业级 AI 工作流架构（FLARE 对齐版）

**演示文档** | 2026-05-08  
**用途**：客户演示 / 内部评审 - FLARE kernel-first、orchestration-first、contract-driven 架构  
**架构等级**：Production-Ready Baseline + Engine Boundary Realignment

---

## 1. 架构定位

小采 AI 助手 1.0 采用 FLARE 架构原则：

- **Kernel 负责权威工作流状态与编排推进**。
- **Engines 负责可复用、确定性的能力函数与契约输出**。
- **Domain Pack / Instance Config 负责业务词汇、流程配置、模板、字段和策略参数**。
- **Runtime / Provider Adapters 负责外部副作用**，包括 LangGraph、Skills、LLM、OCR、Embedding、Search、MCP 等。
- **Storage 只负责持久化承载**，不拥有 workflow 决策。
- **UI 只渲染后端 canonical projection**，不猜测 authoritative state。

---

## 2. 更新后的全局拓扑

```text
[Application / Web UI]
  需求梳理 / 智能寻源 / Project / 知识库 / 使用量管理 / 对话界面
        |
        v
[Transport / API Gateway]
  FastAPI / Auth / Request Mapping / SSE Framing / Response Mapping
        |
        v
[Kernel / Orchestration Core]
  Canonical State / Workflow Progression / Stream Patch Ownership / Error & Retry Policy
        |
        +------------------------------+
        |                              |
        v                              v
[flare-engines]                  [Runtime Adapters]
  Ingestion / Context              LangGraph Runtime
  Memory / Observation             Skills / Tool Actions
  Decision / Execution             Provider Invocation Boundary
  Presentation
  + Analysis / Document Understanding / Ranking / Reasoning / Track Reasoning
        ^                              |
        |                              v
[Domain Pack / Instance Config]   [Provider Adapters]
  workflow / modes / fields         LLM / OCR / Embedding
  templates / policy config         Search / MCP / External APIs
        |
        v
[Storage Ports -> Storage]
  PostgreSQL / Qdrant / Redis / Files / Project Artifacts
```

---

## 3. 核心调用链

1. **UI 发起请求**：用户从对话、需求梳理、智能寻源、Project 或知识库进入。
2. **API 做 transport 映射**：只负责校验、鉴权、SSE/response framing，不做业务编排。
3. **Kernel 推进工作流**：读取 canonical state，调用 engines，决定 runtime adapter 与 patch/event 输出。
4. **Engines 输出标准 contract**：所有能力返回明确 result / event / patch / decision / readiness / confidence。
5. **Domain Pack 注入业务语义**：业务触发词、字段、模板、ranking 权重、mode 映射来自配置。
6. **Adapters 执行外部副作用**：模型、搜索、OCR、Embedding、MCP、LangGraph、Skills 均在 adapter 层。
7. **Storage 持久化承载**：保存会话、知识、向量、Project 归属、结果和运行记录。
8. **Observation 横切可观测**：trace_id 串联日志、事件、成本、健康度和告警。

---

## 4. 七层 Engines 当前职责

| Engine | 责任 | 禁止项 |
|---|---|---|
| Ingestion | 输入标准化、资料接入状态、候选归一化策略 | 不做 provider 调用，不写数据库 |
| Context | 上下文 envelope、token 估算、budget、layer inclusion | 不做 retrieval/provider 决策 |
| Memory | recall 归一化、source refs、dedup、citation | 不实现持久化 |
| Observation | trace/event/citation contract 组装 | 不替代日志平台/监控系统 |
| Presentation | response/event payload 组装 | 不做前端 UI 渲染 |
| Decision | mode/state/policy/readiness/selected_action | 不硬编码业务词 |
| Execution | execution artifact / plan / event assembly | 不直接绑定 LangGraph/Skills SDK |

---

## 5. 与旧图的关键差异

- Presentation Engine 不再等同于 UI Engine；UI 是 presentation layer，engine 是后端 payload assembly。
- Ingestion / Context / Memory / Observation 不再放在“数据存储层”；它们是 reusable capability engines。
- Decision / Execution 不再描述成 Kernel 内部硬编码模块；Kernel 调用 engines public API。
- LangGraph / Skills 不再画进 Execution Engine 内部；它们属于 runtime adapter。
- 业务词汇、触发规则、模板、字段、ranking task profile 由 Domain Pack / Instance Config 提供。

---

**文档状态**：已更新（FLARE 边界对齐版）  
**更新时间**：2026-05-08  
**技术负责人**：CTO  
**用途**：客户演示 / 内部架构评审 / Engine 迁移验收基线
