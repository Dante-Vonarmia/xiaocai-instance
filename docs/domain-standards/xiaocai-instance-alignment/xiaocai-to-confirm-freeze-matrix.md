# xiaocai TO_CONFIRM Freeze Matrix (P0-0)

## Scope

- 冻结日期: 2026-04-10
- 用途: 在不做大实现前，冻结 TO_CONFIRM 决策项、阻塞级别和默认策略。
- 约束: 未确认项只允许占位，不允许脑补业务规则。

---

| Item | Current ambiguity | Why it matters | Blocking level | Suggested default if unresolved | Recommended owner | Recommended deadline |
|---|---|---|---|---|---|---|
| 个人需求识别阈值与提示策略 | 何时判定为“个人需求”、提示文案和跳转动作未定 | 直接影响 entry gate 和分流体验 | BLOCKER | 保守策略: 仅在明确个人消费词触发提示，不强制中断；提供“继续企业场景检索”按钮 | 客户 + 我方产品 | 2026-04-12 |
| 明确意图判定标准 | 关键词 vs 字段完整度 vs 用户确认优先级未定 | 决定是否从检索循环进入梳理/分析/寻源 | BLOCKER | 默认“双条件”: 命中意图词 + 用户确认进入目标阶段 | 客户 + 我方产品 | 2026-04-12 |
| 供应商数量 | 与现有 `候选数量` 是否同义未定 | 影响 sourcing readiness 和 query mapping | BLOCKER | 临时 alias 到 `候选数量`，UI 展示保留“供应商数量(候选数量)” | 客户 + 我方领域 | 2026-04-13 |
| 交期时长 | 与 `交付时间` / `响应时效` 的关系不明 | 影响寻源筛选和模板变量 | BLOCKER | 占位为 derived 字段: 从 `交付时间` 与当前日期计算，缺值不阻断主链 | 客户 + 我方领域 | 2026-04-13 |
| 对标企业 | 是否为新字段、是否进排序因子未定 | 影响 sourcing profile 与检索 query | NON-BLOCKER | 新增 optional 占位字段，不作为 readiness gate | 客户 | 2026-04-15 |
| 员工规模 | 归属买方还是供应商侧未定 | 影响字段语义和数据源映射 | DEFERABLE | optional 占位，不参与排序与 gate | 客户 | 2026-04-15 |
| 买家资金 | 与预算金额关系不明 | 影响字段重复与语义冲突 | DEFERABLE | 暂不新增；必要时以 `预算金额` 代用并标注语义未决 | 客户 + 我方领域 | 2026-04-15 |
| 企业性质 | 枚举口径未定 | 影响 taxonomy、筛选器和模板 | DEFERABLE | optional 占位字段，枚举暂空 | 客户 | 2026-04-15 |
| 社保人数 | 数据源与可信度规则未定 | 影响数据映射和合规 | DEFERABLE | optional 占位字段，不参与 readiness | 客户 | 2026-04-15 |
| 智能寻源 readiness 最小字段集合 | 是否必须含预算/交期、是否允许缺省未定 | 直接决定流程 A 可执行门槛 | BLOCKER | 采用现有 contract 最小集: 一级品类/二级品类/产品服务/交付地点/交付时间/预算金额 | 客户 + 我方领域 | 2026-04-12 |
| 缺失 FLARE 冻结文档跨仓来源位置 | 指定 contract 文档在本仓缺失 | 影响 cross-repo mapping 证据完整性 | NON-BLOCKER | 先按本仓边界文档执行；mapping 标记 pending，不进入平台改造 | cross-repo owner | 2026-04-14 |

---

## Freeze Decision Summary

### BLOCKER（必须先冻结）

1. 个人需求识别阈值与提示策略
2. 明确意图判定标准
3. 供应商数量映射
4. 交期时长映射
5. 智能寻源 readiness 最小字段集合

### NON-BLOCKER（可并行）

1. 对标企业
2. FLARE 缺失文档来源定位

### DEFERABLE（可先占位）

1. 员工规模
2. 买家资金
3. 企业性质
4. 社保人数

---

## As-Is / To-Be / Gap / Next

- As-Is: TO_CONFIRM 项已识别，但未形成统一冻结矩阵。
- To-Be: 所有项具备阻塞级别、默认策略、责任人与截止日期。
- Gap: BLOCKER 项尚未客户签字前，不应进入 P0-1 大实现。
- Next: 先完成 BLOCKER 确认或接受默认策略，再启动 orch policy v1。
