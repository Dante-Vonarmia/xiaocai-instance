# xiaocai Layer Boundary

## Purpose

- 固化 xiaocai 分层职责，避免 orch policy 与 domain pack 混层。
- 固化与 FLARE 的接口边界，明确禁止回灌项。

---

## Layer 1: Orchestration Policy Pack

### 负责什么

1. entry rules（企业场景校准、个人需求提醒策略）
2. intent bias（无意图继续检索、有意图分流）
3. mode suggestion rules（推荐进入 requirement/analysis/sourcing）
4. field gate rules（何时阻断、何时继续澄清）
5. transition rules（阶段进入/回退）
6. analysis readiness / sourcing readiness rules
7. output profile selection（按状态选输出形态）

### 不负责什么

1. 字段业务语义定义
2. 品类字典维护
3. 模板变量词典本身
4. 平台级会话/SSE 协议

### 当前状态

- `PARTIAL`: 在 `domain-pack/workflows/procurement-workflow-nodes.yaml` 有结构雏形。
- `DOC_ONLY`: 运行时执行器证据不足（adapter/web 未见消费）。

### 优先级

- `P0`（必须先建设），否则 To-Be 流程无法稳定执行。

---

## Layer 2: Domain Pack

### 负责什么

1. 字段语义（field dictionary）
2. 品类体系（category taxonomy）
3. terminology / alias
4. 模板变量定义与依赖
5. query mapping / replace rules
6. 文案素材、推荐语料、场景 fixture

### 不负责什么

1. API 请求转发
2. 鉴权与 project ownership
3. UI 状态机实现

### 当前状态

- `IMPLEMENTED`: 配置资产齐全（schema/workflow/contracts/scenarios/cards/terminology）。
- `PARTIAL`: 与客户新增字段存在映射空缺。

### 优先级

- `P0-P1`: 先补字段与策略映射，再扩展品类细化。

---

## Layer 3: Data Contract / Data Mapping Layer

### 负责什么

1. domain 字段到 kernel context/workspace state 的映射约定
2. replace_history / evidence 可追溯结构
3. analysis/rfx 输出与字段快照关联

### 不负责什么

1. 业务流程编排决策本身
2. 前端展示样式

### 当前状态

- `PARTIAL`: `domain-pack/contracts/flare-contract-mapping.yaml` 已定义，但状态为 `pending_flare_validation`。

### 优先级

- `P0`: 先打通关键映射，否则 policy 无法落地到运行态。

---

## Layer 4: Output Templates / Profiles

### 负责什么

1. requirement-analysis 章节结构
2. RFI/RFQ/RFP/RFB 模板依赖
3. 草稿态/确认态输出规则

### 不负责什么

1. 模板触发时机（由 orchestration 决定）
2. UI 路由与页面流

### 当前状态

- `IMPLEMENTED`（配置层）: `procurement-analysis-rfx-templates.yaml`。
- `PARTIAL`（执行层）: 是否在运行态强制字段阻断待验证。

### 优先级

- `P1`: 在 P0 policy/data 映射后接入执行。

---

## Layer 5: UI / Application Mapping

### 负责什么

1. 将 backend/kernel 事件映射到 ChatWorkspace 交互
2. starter prompts、ui labels、identity context 装配
3. project/session/source/artifact 操作入口

### 不负责什么

1. 采购业务规则解释器
2. 字段语义定义

### 当前状态

- `IMPLEMENTED`: frame + adapter 基础壳可运行。
- `DRIFTED`: 前端内置默认 prompts 与 domain-pack 双源并存。

### 优先级

- `P2`: 在 policy 稳定后收敛配置单源。

---

## Layer 6: FLARE Interface Boundary

### xiaocai 可以做

1. 通过公开 context/contract 接口传入业务约束。
2. 在 instance 侧维护 procurement domain 资产。
3. 在 adapter/web 做权限、会话、项目隔离。

### xiaocai 不能做（Hard Boundary）

1. 改写 FLARE kernel contract（`OUT_OF_SCOPE`）。
2. 在 FLARE 通用层硬编码采购语义（`OUT_OF_SCOPE`）。
3. 在 instance 重写平台状态机/SSE 协议（`OUT_OF_SCOPE`）。
4. 以 xiaocai 诉求反向重构 FLARE 通用逻辑（除非确认平台能力缺口）。

### 当前状态

- `IMPLEMENTED`: `docs/architecture/07-flare-instance-boundary.md` 已明确原则。
- `RISK`: 缺少正式 kernel-contract 文档副本，跨仓对齐需补证据链。

---

## As-Is / To-Be / Gap / Next

- As-Is: 分层概念齐全，但 orch policy 与 data mapping 运行闭环未成形。
- To-Be: policy/domain/data/template/ui 各层独立、通过 contract 对接 FLARE。
- Gap: P0 缺口集中在 policy 执行与 mapping 验证，而非 UI 壳本身。
- Next: 先补 P0（policy pack + mapping），再做 P1（模板执行）与 P2（UI 收敛）。
