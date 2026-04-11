# xiaocai Target Flow Spec (To-Be)

## Scope

- 来源: 客户最终确认流程（本轮输入）
- 目标: 把流程图语言翻译为可实现结构，不直接写代码。

---

## A. Entry / Intent Policy

### A1 Entry Rules

1. 进入会话先执行意图识别与目的识别。
2. 若识别为个人消费/个人需求，先提示“小采是企业采购场景辅助工具”。
3. 提供两条入口动作:
- 继续在企业场景下进行智能检索
- 跳转使用现有小采功能（由产品定义具体入口）

状态:
- `TO_CONFIRM`: “个人需求”判定阈值、提示文案、跳转动作枚举。

### A2 Intent Bias

- 无明确意图: 保持在“智能检索澄清循环”。
- 明确意图: 可建议进入以下目标之一:
  - 需求梳理
  - 需求分析
  - 智能寻源

状态:
- `TO_CONFIRM`: “明确意图”判定规则（关键词、结构字段完成度、用户显式确认优先级）。

---

## B. Core Fields (进入需求梳理或智能寻源前)

必确认字段（流程 A/B 一致）:

1. 采购目的
2. 使用场景
3. 一级品类
4. 二级品类
5. 交付地点

---

## C. Optional / Enhancement Fields

### C1 智能寻源附加字段

1. 产品/服务
2. 供应商区域
3. 供应商数量
4. 交期时长
5. 对标企业
6. 可选增强:
- 员工规模
- 买家资金
- 企业性质
- 社保人数

### C2 需求梳理附加字段

1. 交付时间
2. 预算金额
3. 产品/服务
4. 数量单位
5. 细化字段:
- 产品/服务说明
- 特殊要求

### C3 需求梳理标准输出建议字段

1. 项目名称
2. 需求来源
3. 需求提出人
4. 影响范围

---

## D. Gate Policy

### D1 Entry Gate

- 未完成 Core Fields，不允许直接进入高置信度寻源推荐。
- 未完成 Core Fields，可继续智能检索澄清。

### D2 Requirement-Collection Gate

- 需求梳理模板字段需达到“最小可分析集合”后才可进入需求分析。

### D3 Analysis Gate

- 需求分析阶段需补齐：技术要求、质量标准、验收口径、交付方式、发票类型、付款条款、关键条款。
- 条件具备后可建议进入智能寻源或 RFX 策略。

状态:
- `TO_CONFIRM`: 每个 gate 的最小字段集合与阻断提示文案。

---

## E. Transition Policy

### E1 智能检索主循环

- `search_clarification -> search_clarification`（无明确意图或关键字段不足）
- `search_clarification -> requirement_collection`（意图明确且用户选择）
- `search_clarification -> requirement_analysis`（已有较完整需求）
- `search_clarification -> intelligent_sourcing`（寻源意图明确且前置字段已达标）

### E2 需求链路

- `requirement_collection -> requirement_analysis`
- `requirement_analysis -> rfx_strategy`
- `requirement_analysis -> intelligent_sourcing`（条件具备时）
- 任意阶段允许回退到上游补字段

状态:
- `TO_CONFIRM`: 进入 `intelligent_sourcing` 的 readiness 条件是否必须包含预算/交付时间。

---

## F. Output Profiles

### F1 Search Clarification Profile

- 输出: 识别结果、缺失字段、下一步建议动作。
- 禁止: 在字段不足时输出完整策略结论。

### F2 Requirement Collection Profile

输出模板至少包含:

1. 项目名称
2. 项目概述
3. 采购目的
4. 使用场景
5. 预算金额
6. 交付地点
7. 交付时间
8. 需求部门信息（如有）
9. 需求来源
10. 需求提出人
11. 影响范围
12. 一级品类
13. 二级品类
14. 细化需求:
- 产品/服务
- 数量单位
- 产品/服务说明
- 特殊要求

### F3 Requirement Analysis Profile

- 输出: 分析结论 + 风险 + 条款建议 + RFX 支撑信息。
- 必含补充方向: 技术要求、质量标准、验收口径、交付方式、发票类型、付款条款、关键条款。

### F4 RFX Support Profile

- 输出目标: 为 RFX 策略决策提供结构化输入。
- 不等价于直接生成最终法务文件。

---

## G. Sourcing Profile

建议结构:

1. 输入约束摘要（品类/场景/预算/地点/交付）
2. 候选池说明（数量、区域、是否新供应商）
3. 推荐理由（可追溯字段）
4. 风险提示
5. 下一步动作（比价、补字段、进入 RFX）

状态:
- `TO_CONFIRM`: 对标企业、买家资金等字段是否硬性参与排序。

---

## H. Analysis Profile

建议结构:

1. 项目理解
2. 需求可行性
3. 市场/供应分析输入
4. 风险与验收口径
5. 条款与付款发票建议
6. 是否满足进入寻源/RFX 的 readiness 结论

---

## I. RFX Support Profile

建议结构:

1. RFX 类型建议（RFI/RFQ/RFP/RFB）
2. 触发理由与前提字段
3. 必填缺口
4. 输出形式建议

状态:
- `TO_CONFIRM`: 类型选择策略（规则优先还是用户选择优先）。

---

## J. TO_CONFIRM List (must not guess)

1. “个人需求”识别规则与提示策略。
2. “明确意图”判定标准与最低置信阈值。
3. `供应商数量` 是否直接映射现有 `候选数量`。
4. `交期时长` 是否直接映射现有 `交付时间`（或新增字段）。
5. `对标企业` 是否作为新字段进入 field dictionary。
6. `员工规模/买家资金/企业性质/社保人数` 的来源与校验口径。
7. 进入智能寻源的最小 readiness 字段集合。
8. 需求部门信息字段是否拆分为独立字段或继续可选文本。

---

## K. P0-0 Freeze Defaults (for pre-implementation only)

以下默认值仅用于进入 P0-1 前的准备轮，不代表最终客户确认规则:

1. `供应商数量` 默认映射为 `候选数量`（alias）。
2. `交期时长` 默认作为 derived 字段（基于 `交付时间` 与当前日期计算）。
3. `对标企业` 先作为 optional 占位，不纳入 readiness gate。
4. `员工规模/买家资金/企业性质/社保人数` 标记 optional+defer，不进入 v1 强规则。
5. 智能寻源 readiness 先采用现有 contract 最小集:
- 一级品类
- 二级品类
- 产品/服务
- 交付地点
- 交付时间
- 预算金额

冻结矩阵详见:
- `docs/domain-standards/xiaocai-instance-alignment/xiaocai-to-confirm-freeze-matrix.md`
- `docs/domain-standards/xiaocai-instance-alignment/xiaocai-field-mapping-closure-spec.md`

---

## As-Is / To-Be / Gap / Next

- As-Is: 有 workflow/field/template 契约，但运行态编排执行证据不足。
- To-Be: 形成 entry->clarify->collection->analysis->sourcing/rfx 的可执行 policy 结构。
- Gap: 客户流程中若干字段和 gate 规则尚未映射到正式 taxonomy，且存在 BLOCKER 级 TO_CONFIRM。
- Next: 先完成 P0-0 freeze + P0-2 mapping closure，再进入 orch policy v1。
