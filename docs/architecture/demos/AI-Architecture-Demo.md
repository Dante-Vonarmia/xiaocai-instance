# 小采 AI 助手 1.0 企业级 AI 工作流架构（Field Agent 协议同步版）

**演示文档** | 2026-05-11  
**用途**：客户演示 / 内部评审 - FLARE Kernel、Runtime Agent、Field Agent、Capability、Engine 标准协议  
**架构等级**：生产级基线 + Field Agent 可交付协议

---

## 1. 架构定位

小采 AI 助手 1.0 采用 FLARE 最新 Field Agent 口径：

- **Surface** 是 Workbench、Canvas、Inventory 等交互入口，只呈现 Runtime 投影，不发明权威状态。
- **Kernel** 负责组装、调度、状态推进、事件输出和恢复。
- **Runtime Agent Class** 是 Kernel 内的系统级运行单元，负责状态、生命周期、策略执行与事件流。
- **Field Agent Class** 是面向业务现场的可实例化 Agent，由 Runtime 调度执行。
- **Capability** 是 Field Agent 可调用的能力合同，不归属 Agent Class 命名体系。
- **Engine** 是底层可替换实现，例如检索、分析、OCR、模型推理和文档生成。
- **Domain Pack** 提供行业 know-how、字段、流程、规则、SOP 和案例资产。
- **Tool / Adapter** 是外部系统或 Provider 的接入边界，必须归一化后进入 Runtime。

---

## 2. 更新后的全局拓扑

```text
[1. Surface / 展现层]
  Workbench / Canvas / Inventory
  Input: UserAction / ProjectContext / AttachmentRef
  Output: RuntimeProjection / SurfaceEvent
        |
        v
[2. 传输 / API 网关]
  Input: SurfaceEvent
  Output: StandardRequest / SSE Frame / StandardResponse
        |
        v
[3. Kernel / 编排核心]
  Input: StandardRequest + Canonical State + Domain Pack
  Responsibility: 组装 Runtime、Field Agent、Capability、Engine、Surface
  Output: RuntimeDispatch / Event / Patch / Projection / Recovery Signal
        |
        v
[4. Runtime Agent / Field Agent]
  Runtime Agent: 状态、生命周期、策略执行、事件流
  Field Agent: manifest、input_contract、output_contract、bindings、handoff、failure
  Field Agent -> CapabilityRequest -> Engine / Tool -> FieldAgentResult
        |
        v
[5. Runtime / Provider 适配器]
  Tool / Adapter: LLM / OCR / Search / MCP / External APIs
  Output: Normalized Provider Result / Failure Signal
        |
        v
[6. 存储 / 基础设施]
  PostgreSQL / Qdrant / Redis / 文件 / 项目产物

横切治理：安全合规 / 网络与链路监控 / 性能与链路优化 / 发布与质量门禁 / 运行可靠性
```

---

## 3. 主链路 Input / Output 标准口径

| 节点 | 输入 | 责任 | 输出 | 禁止项 |
|---|---|---|---|---|
| Surface | 用户动作、项目上下文、文件与表单 | 展示 Runtime 投影，收集用户动作 | SurfaceEvent、UserAction、AttachmentRef | 不猜测权威状态 |
| API | SurfaceEvent、附件引用、用户身份 | 校验、鉴权、请求映射、SSE 封装 | StandardRequest、StandardResponse、SSE Frame | 不做业务编排 |
| Kernel | StandardRequest、Canonical State、Domain Pack | 组装 Runtime / Agent / Capability / Engine，推进状态与恢复 | RuntimeDispatch、Event、Patch、RuntimeProjection | 不把业务流程 hardcode |
| Runtime Agent | RuntimeDispatch、状态策略、生命周期策略 | 调度 Field Agent，管理暂停、恢复、事件流 | FieldAgentAssignment、RuntimeEvent、RecoverySignal | 不承载业务 know-how |
| Field Agent | FieldAgentAssignment、input_contract、Domain Pack | 执行业务现场任务，绑定 Capability / Engine / Tool | FieldAgentResult、FailureContract、HandoffPolicy | 不直接依赖 Provider 原始返回 |
| Capability | CapabilityRequest | 定义能力合同、输入输出和验收边界 | CapabilityResult | 不替代 Engine 实现 |
| Engine | CapabilityRequest、标准上下文 | 执行检索、分析、OCR、推理、文档生成等底层能力 | Typed CapabilityResult | 不拥有工作流状态 |
| Tool / Adapter | ToolIntent、Provider 参数 | 接入外部系统，归一化 Provider 返回 | Normalized Provider Result、失败 / 重试信号 | 不把原始 Provider payload 直接交给领域逻辑 |
| Storage | StorageCommand、结果对象、索引对象 | 保存状态、知识、向量、项目归属与产物 | StoredRecord、ArtifactRef、IndexRef | 不决定业务状态推进 |

---

## 4. Field Agent 可交付协议字段

| 字段 | 作用 |
|---|---|
| agent_id / class / domain / version | 标识 Agent、归属 Field Agent Class、行业范围与版本。 |
| purpose | 说明业务目标，避免 Agent 变成一次性 Prompt。 |
| input_contract | 定义可接受输入、上下文、附件和前置条件。 |
| output_contract | 定义标准输出、结果结构、解释信息和交付对象。 |
| capability_bindings | 声明可调用的 Capability 列表。 |
| engine_bindings | 声明可调用或依赖的 Engine 列表。 |
| tool_bindings | 声明可调用的 Tool / Adapter 列表。 |
| runtime_contract | 定义 Runtime 如何调度、暂停、恢复和接收结果。 |
| state_policy | 定义状态推进规则。 |
| handoff_policy | 定义与其他 Agent、人工节点或 Surface 的交接规则。 |
| failure_contract | 定义失败、降级、重试和不可完成结果。 |
| governance_metadata | 定义 Owner、状态、权限、审计和适用范围。 |

---

## 5. 横切治理能力的作用域

| 治理维度 | 覆盖范围 | 关键作用 |
|---|---|---|
| 安全与合规 | 用户、租户、数据、模型调用与审计 | 建立身份、权限、数据边界与审计闭环 |
| 网络与链路监控 | 浏览器入口、API、SSE、Provider 调用链 | 监测链路健康、时延波动、错误分布与外部依赖状态 |
| 性能与链路优化 | 并发、队列、缓存、模型成本与降级路径 | 优化响应时延、吞吐能力、资源利用率与降级策略 |
| 发布与质量门禁 | 代码、配置、契约、镜像与上线流程 | 约束变更准入、发布节奏、灰度策略与回滚路径 |
| 运行可靠性 | 容器、日志、资源、备份与故障恢复 | 保障服务连续性、故障定位效率与恢复能力 |

---

## 6. 为什么和最初 7 层不一样

- 当前主图是 **6 层产品 / 系统架构**：Surface、API、Kernel、Runtime Agent / Field Agent、Runtime / Provider、Storage。
- 本仓库最初 demo 可追溯版本里的“7”是 **七个 Engine 能力职责**：Ingestion、Context、Memory、Observation、Presentation、Decision、Execution。
- 最初 demo 已经把 Application / Web UI 放在同一层，不是应用层与展现层拆分。
- 最新口径下，Field Agent 是可交付、可实例化、可治理的业务现场 Agent；Engine 是其可调用的底层能力实现。
- Capability、Engine、Tool 可以替换，但 Field Agent 的 input_contract / output_contract / runtime_contract 必须稳定。

---

**文档状态**：已更新（Field Agent 协议同步版）  
**更新时间**：2026-05-11  
**技术负责人**：CTO  
**用途**：客户演示 / 内部架构评审 / Field Agent 协议验收基线
