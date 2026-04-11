# xiaocai Backlog (Post-Alignment)

## Scope

- 目标: 支撑客户最终流程开发，不越界到 FLARE 基座改造。
- 原则: 先文档与契约闭环，再最小实现闭环。

---

## Priority Legend

- P0: 阻断项，必须先做
- P1: 主链路能力项
- P2: 体验与扩展项
- P3: 延后项

---

## Task 0 (P0-0) - TO_CONFIRM Freeze Matrix

- Title: 冻结 TO_CONFIRM 决策矩阵
- Why: 未冻结的字段与判定规则会直接导致 orch policy 返工
- Goal: 给每个 TO_CONFIRM 项定义 blocking level/default/owner/deadline
- Scope:
  - 冻结 11 项关键 TO_CONFIRM
  - 定义 BLOCKER/NON-BLOCKER/DEFERABLE
- Out of Scope:
  - orch policy 代码实现
- Affected Areas:
  - `docs/domain-standards/xiaocai-instance-alignment/xiaocai-to-confirm-freeze-matrix.md`
- Dependencies:
  - 客户流程最终口径同步
- Acceptance Criteria:
  - 每项都有默认策略和责任人
  - BLOCKER 项有明确截止日期
- Risk:
  - 跨角色未按时确认
- Priority: P0
- Suggested Order: 0
- Type: `preparation / governance`

---

## Task 1 (P0-2) - Field Mapping Closure Prep

- Title: 字段映射收口准备（Field Mapping Closure Prep）
- Why: 客户新增字段映射未稳，直接做 policy 会返工
- Goal: 形成字段映射闭包（reuse/alias/new/derived/defer）与影响面清单
- Scope:
  - 完成 mapping closure table
  - 输出“可立即开发/必须确认/可占位/defer”分组
- Out of Scope:
  - orch policy 实现
- Affected Areas:
  - `docs/domain-standards/xiaocai-instance-alignment/xiaocai-field-mapping-closure-spec.md`
  - `docs/domain-standards/xiaocai-instance-alignment/xiaocai-field-taxonomy.md`
  - `docs/domain-standards/xiaocai-instance-alignment/*`
- Dependencies:
  - Task 0
- Acceptance Criteria:
  - 新增字段均有 mapping type
  - 明确是否影响 core/sourcing/analysis/template/flare mapping
- Risk:
  - 别名与新增字段混用造成后续漂移
- Priority: P0
- Suggested Order: 1
- Type: `field taxonomy / schema`

---

## Task 2 (P0-1) - xiaocai Orch Policy Pack v1

- Title: 定义并落盘 xiaocai orchestration policy 配置
- Why: 需要把 gate/transition/readiness 变为可执行 policy
- Goal: 形成 entry/intent/gate/transition/readiness/output-profile 的统一 policy 文件
- Scope:
  - 定义 entry rules
  - 定义 intent bias
  - 定义 mode suggestion rules
  - 定义 analysis/sourcing readiness rules
- Out of Scope:
  - kernel 内部状态机改造
  - FLARE contract 变更
- Affected Areas:
  - `domain-pack/workflows/*`（新 policy 配置文件或扩展）
  - `docs/domain-standards/xiaocai-instance-alignment/*`
- Dependencies:
  - Task 0 与 Task 1 完成
- Acceptance Criteria:
  - policy 文件可读、可校验、可映射到现有 workflow 节点
  - 每条 transition 都有进入条件与回退条件
- Risk:
  - 规则过强导致误阻断
- Priority: P0
- Suggested Order: 2
- Type: `orch policy`

---

## Task 3 (P0) - FLARE Mapping Validation Plan

- Title: 合同映射验证计划（不改 FLARE）
- Why: 当前 `flare-contract-mapping.yaml` 全部 pending
- Goal: 明确每个 mapping 的验证路径、fallback 与责任边界
- Scope:
  - 对 `search_tasks` / `replace_history` / `analysis_template` / `rfx_template` 做映射验收计划
  - 产出 gap 记录模板
- Out of Scope:
  - 改写 kernel contract
- Affected Areas:
  - `domain-pack/contracts/flare-contract-mapping.yaml`
  - `docs/domain-standards/08-domain-adr-index.md`
  - `docs/domain-standards/09-domain-implementation-backlog.md`
- Dependencies:
  - 可访问 FLARE contract 文档
- Acceptance Criteria:
  - 每个映射项都有“已验证/待验证/不可达”状态
  - 发现 gap 时仅更新 contract 与 ADR，不发起平台重写
- Risk:
  - 跨仓信息不完整导致误判
- Priority: P0
- Suggested Order: 3
- Type: `data mapping / ingestion`

---

## Task 4 (P1) - Target Flow Profiles Formalization

- Title: 输出 profile 正式化（search/collection/analysis/sourcing/RFX）
- Why: 客户流程要求按阶段输出，不是统一自由文本
- Goal: 形成 profile 配置与最小输出契约
- Scope:
  - 定义 profile 触发条件
  - 定义每个 profile 最小输出字段
  - 绑定模板变量
- Out of Scope:
  - 文档渲染 UI 大改
- Affected Areas:
  - `domain-pack/contracts/procurement-analysis-rfx-templates.yaml`
  - `domain-pack/contracts/procurement-search-sourcing-replace.yaml`
- Dependencies:
  - Task 1/2
- Acceptance Criteria:
  - 缺关键字段时输出缺口清单而非完整报告
  - 模板变量零悬空
- Risk:
  - profile 过多导致策略冲突
- Priority: P1
- Suggested Order: 4
- Type: `template/output profile`

---

## Task 5 (P1) - Sourcing Readiness & Gate Enforcement

- Title: 智能寻源 readiness 最小闭环
- Why: 客户流程 A 需要“检索->寻源”的明确 gate
- Goal: 建立可执行的寻源前置字段 gate 与推荐输出结构
- Scope:
  - 固化 sourcing required fields
  - 固化 candidate_pool_policy 与 explainability 结构
- Out of Scope:
  - 供应商排名模型优化
- Affected Areas:
  - `domain-pack/contracts/procurement-search-sourcing-replace.yaml`
  - `domain-pack/workflows/procurement-workflow-nodes.yaml`
- Dependencies:
  - Task 1/2
- Acceptance Criteria:
  - 字段不足时明确阻断并给补齐指引
  - 推荐输出含理由与风险字段
- Risk:
  - 过早放开导致“字段不足即推荐”回归
- Priority: P1
- Suggested Order: 5
- Type: `orch policy` + `domain pack`

---

## Task 6 (P1) - Analysis to RFX Chain Alignment

- Title: 需求分析 -> RFX 支撑链路对齐
- Why: 客户流程 B 要求 analysis 补充并支撑 RFX
- Goal: 强化 analysis 必填和 RFX 支撑关系
- Scope:
  - 分析字段依赖矩阵校准
  - RFX 类型建议前提字段校准
- Out of Scope:
  - 法务终版合同生成
- Affected Areas:
  - `domain-pack/contracts/procurement-analysis-rfx-templates.yaml`
  - `domain-pack/workflows/procurement-workflow-nodes.yaml`
- Dependencies:
  - Task 1/2/4
- Acceptance Criteria:
  - analysis 缺口可解释
  - RFX 建议可追溯到字段
- Risk:
  - 模板与 workflow 条件不一致
- Priority: P1
- Suggested Order: 6
- Type: `template/output profile` + `orch policy`

---

## Task 7 (P2) - UI/Application Adaptation

- Title: 实例 UI 配置单源化（减少 drift）
- Why: 前端默认配置与 domain-pack 双源并存
- Goal: 将 starter prompts / labels 尽量从 domain-pack 读取，减少硬编码
- Scope:
  - 收敛 prompts 来源
  - 评估 mode 入口提示的配置化
- Out of Scope:
  - 重写 ChatWorkspace
- Affected Areas:
  - `frame/web/src/pages/ChatPage.tsx`
  - `domain-pack/branding/instance-branding.json`
- Dependencies:
  - Task 1/4
- Acceptance Criteria:
  - prompts/labels 单源可追溯
- Risk:
  - 兼容历史 fallback 行为
- Priority: P2
- Suggested Order: 7
- Type: `UI/application adaptation`

---

## Task 8 (P1) - Domain Tests/Eval Upgrade

- Title: 场景验收与策略断言升级
- Why: 目前主要是 API 通路测试，不足以证明业务流程对齐
- Goal: 增加 orch policy 与字段 gate 的可回归断言
- Scope:
  - 5 个核心场景补 transition/gate/profile 断言
  - 补字段映射回归用例
- Out of Scope:
  - 大规模性能压测
- Affected Areas:
  - `domain-pack/contracts/scenarios/*.yaml`
  - `adapters/http_api/tests/*`（增加契约级断言）
- Dependencies:
  - Task 1/2/4/5/6
- Acceptance Criteria:
  - 关键场景可自动判定通过/失败
- Risk:
  - mock kernel 与真实 kernel 行为差异
- Priority: P1
- Suggested Order: 8
- Type: `tests / eval`

---

## Deferred Items

1. 全品类 category-specific 字段批量填充
- 标签: `DEFERRED`

2. 供应商排序模型精细化、阈值学习
- 标签: `DEFERRED`

3. 非首轮流程节点（quotation/negotiation/contract/delivery）实现
- 标签: `DEFERRED`

4. 任何 FLARE contract / kernel state ownership 改造
- 标签: `OUT_OF_SCOPE`

---

## Suggested Implementation Order (Minimal Closed Loop)

1. Task 0 - TO_CONFIRM freeze
2. Task 1 - 字段映射收口
3. Task 2 - orch policy pack v1
4. Task 3 - flare mapping validation
5. Task 5 - 检索->寻源 gate 最小闭环
6. Task 6 - 需求分析->RFX 支撑闭环
7. Task 8 - 场景回归断言
8. Task 4 - profile 正式化补强
9. Task 7 - UI 单源收敛

---

## First-Batch Minimal Closed Loop

目标链路:

- `智能检索澄清 -> 需求梳理 ->（字段达标）-> 智能寻源建议`

最小字段:

1. 采购目的
2. 使用场景
3. 一级品类
4. 二级品类
5. 交付地点
6. 产品/服务
7. 预算金额
8. 交付时间

最小验收:

1. 字段不达标时不会直接寻源
2. 达标后返回结构化候选与理由
3. replace history 可追溯

---

## As-Is / To-Be / Gap / Next

- As-Is: 已有 backlog 基础条目，但未按客户最终流程进行 P0/P1 精排。
- To-Be: 形成 `P0-0 -> P0-2 -> P0-1` 的前置顺序，避免 policy 返工。
- Gap: BLOCKER 级 TO_CONFIRM 未冻结前，无法安全进入 P0-1。
- Next: 先完成 Task 0/1，再启动 Task 2。
