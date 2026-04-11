# xiaocai Field Mapping Closure Spec (P0-2 Prep)

## Scope

- 目标: 在不做大实现前，把客户新增字段与现有 taxonomy 的映射收口到可进入 `orch policy v1`。
- 来源: 客户流程字段 + `domain-pack/schema/procurement-field-dictionary.yaml` + `domain-pack/contracts/*.yaml`。

---

## Mapping Type Definition

1. `reuse`: 直接复用现有字段
2. `alias`: 客户字段作为现有字段别名
3. `new`: 需要新增字段
4. `derived`: 由现有字段计算得到
5. `defer`: 暂不进入 v1 主链

---

## Closure Table

| 客户字段名 | 当前 taxonomy 是否已有对应 | 当前对应字段路径/证据 | Mapping type | 是否影响 core required | 是否影响 sourcing readiness | 是否影响 analysis/template | 是否影响 FLARE mapping | 当前状态标签 |
|---|---|---|---|---|---|---|---|---|
| 采购目的 | 有 | `schema/procurement-field-dictionary.yaml` + `schema/procurement.yaml#stage_field_sets` | reuse | 是 | 是 | 是 | 是 | IMPLEMENTED |
| 使用场景 | 有 | 同上 | reuse | 是 | 是 | 是 | 是 | IMPLEMENTED |
| 一级品类 | 有 | 同上；`contracts/procurement-search-sourcing-replace.yaml#required_requirement_fields` | reuse | 是 | 是 | 是 | 是 | IMPLEMENTED |
| 二级品类 | 有 | 同上 | reuse | 是 | 是 | 是 | 是 | IMPLEMENTED |
| 交付地点 | 有 | `schema/*.yaml` + `contracts/procurement-search-sourcing-replace.yaml` | reuse | 是 | 是 | 是 | 是 | IMPLEMENTED |
| 供应商数量 | 部分（有 `候选数量`） | `schema/procurement-field-dictionary.yaml` 存在 `候选数量` | alias（默认） | 否 | 是 | 否 | 是 | TO_CONFIRM / PARTIAL |
| 交期时长 | 无同名（有 `交付时间`、`响应时效`） | `schema/procurement-field-dictionary.yaml` 存在 `交付时间`、`响应时效` | derived（默认） | 否 | 是 | 可能 | 是 | TO_CONFIRM / PARTIAL |
| 对标企业 | 无 | dictionary 未命中 | new（optional） | 否 | 是（增强） | 否 | 可能 | TO_CONFIRM |
| 员工规模 | 无 | dictionary 未命中 | new（optional） | 否 | 否（v1） | 否 | 否（v1） | DEFERRED / TO_CONFIRM |
| 买家资金 | 无明确同名（可能与预算金额语义重叠） | `预算金额` 已存在于 dictionary | defer（默认） | 否 | 否（v1） | 否 | 否（v1） | DEFERRED / TO_CONFIRM |
| 企业性质 | 无 | dictionary 未命中 | new（optional） | 否 | 否（v1） | 否 | 否（v1） | DEFERRED / TO_CONFIRM |
| 社保人数 | 无 | dictionary 未命中 | new（optional） | 否 | 否（v1） | 否 | 否（v1） | DEFERRED / TO_CONFIRM |

---

## Impact Summary

### 对 core required fields 的影响

- 直接影响且已稳定: 采购目的、使用场景、一级品类、二级品类、交付地点。
- 新增字段均不应在 v1 直接升级为 core required（避免阻断主链）。

### 对 sourcing readiness 的影响

- v1 必须稳定: 一级品类、二级品类、产品/服务、交付地点、交付时间、预算金额。
- 待确认但可占位: 供应商数量(alias 候选数量)、交期时长(derived)。
- 可 deferred: 对标企业/员工规模/买家资金/企业性质/社保人数。

### 对 analysis/template 的影响

- 本轮新增字段不应成为 analysis/RFX 模板必填。
- 若后续要求入模板，需先完成字段口径确认和变量绑定。

### 对 FLARE mapping 的影响

- 影响最小且可先走: 供应商数量(alias)、交期时长(derived) 映射说明。
- 新增可选字段默认不进入首批 FLARE mapping。

---

## Closure Output (for P0-1 gate)

### 可立即进入 orch policy v1 的字段策略

1. `供应商数量 -> alias 候选数量`
2. `交期时长 -> derived(交付时间, 当前时间)`
3. `对标企业` 作为 optional 占位，不阻断流程

### 必须确认后再升级为强规则的字段策略

1. 对标企业是否进入排序因子
2. 员工规模/买家资金/企业性质/社保人数是否进入 readiness

---

## As-Is / To-Be / Gap / Next

- As-Is: 新增字段映射散落在 TO_CONFIRM 语句，未形成统一闭包。
- To-Be: 每个新增字段都有 mapping type + 影响面 + v1 策略。
- Gap: 仍需客户确认 optional 字段的业务地位。
- Next: 以本 spec 为 P0-1 前置输入，先做可立即项，延后可 defer 项。
