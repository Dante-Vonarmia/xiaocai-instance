# xiaocai Field Taxonomy

## Scope

- 目标: 形成客户流程可实现字段结构，不把未确认字段直接写死为已实现。
- 来源: 客户 To-Be 流程 + 现有 `domain-pack/schema/procurement-field-dictionary.yaml`。

---

## 1) Core Required Fields

进入需求梳理或智能寻源前最小必需字段:

1. 采购目的
2. 使用场景
3. 一级品类
4. 二级品类
5. 交付地点

现状映射:
- `IMPLEMENTED`: 上述 5 项均已在 field dictionary 中存在。

---

## 2) Recommended Fields

建议在需求梳理阶段优先补齐:

1. 交付时间
2. 预算金额
3. 产品/服务
4. 数量
5. 单位
6. 项目名称
7. 需求来源
8. 需求提出人
9. 影响范围（部门/区域）
10. 产品/服务 说明
11. 特殊要求

现状映射:
- `IMPLEMENTED`: 以上字段在现有 dictionary/scheme 大部分已存在。

---

## 3) Optional Fields (客户增强项)

客户提出的增强字段:

1. 供应商数量
2. 交期时长
3. 对标企业
4. 员工规模
5. 买家资金
6. 企业性质
7. 社保人数

现状映射:

- `候选数量` 已存在，是否映射到 `供应商数量` -> `TO_CONFIRM`
- `交付时间` 已存在，是否可承载 `交期时长` -> `TO_CONFIRM`
- `对标企业` 未见同名字段 -> `PARTIAL`
- `员工规模/买家资金/企业性质/社保人数` 未见同名字段 -> `PARTIAL`

处理建议:
- 未确认前标记 `TO_CONFIRM`，不直接落为强校验必填。

---

## 4) Category-Specific Additions

- 现状: `domain-pack/category-fields/procurement-category-fields.yaml` 已建立三级目录并保留占位。
- 状态: `PARTIAL`

占位键:

1. 各品类特殊需求字段占位
2. 各品类特殊寻源要素占位

建议:
- 先对“服务器/活动执行/礼品定制/内容制作/差旅服务”五个场景填首批 special fields。

---

## 5) Sourcing Fields

建议最小寻源字段集:

1. 一级品类
2. 二级品类
3. 产品/服务
4. 交付地点
5. 交付时间
6. 预算金额
7. 供应商区域
8. 候选数量（或供应商数量映射）
9. 允许新供应商

现状映射:
- `IMPLEMENTED`: 1-6、7、8（候选数量）、9 在现有配置可找到。
- `TO_CONFIRM`: 客户口径“供应商数量”是否统一为“候选数量”。

---

## 6) Analysis Fields

需求分析/RFX支撑关键字段:

1. 技术要求
2. 质量标准
3. 验收口径
4. 交付方式
5. 发票类型
6. 付款条款
7. 关键条款
8. 风险等级
9. 风险分析

现状映射:
- `IMPLEMENTED`: 上述字段均在 dictionary/workflow/templates 中已有。

---

## 7) Template Variables

RFX 变量绑定现状（示例）:

- RFI: `project_name`, `objective`, `category_l1`, `category_l2`, `item`, `deliverable`, `format`
- RFQ: `item`, `quantity`, `unit`, `delivery_time`, `delivery_place`, `payment_terms`, `invoice_type`
- RFP: `tech_requirements`, `quality_standard`, `acceptance_criteria`, `evaluation_items`, `weights`
- RFB: `milestones`, `approver`

状态:
- `IMPLEMENTED`: 模板变量与字段绑定已定义。
- `PARTIAL`: 与客户新增字段（如对标企业）尚无绑定策略。

---

## 8) Taxonomy Alias / Terminology

- 现状: `domain-pack/terminology/procurement.yaml` 已有 intents/synonyms。
- 缺口: 未见客户新增词汇（对标企业、买家资金等）术语映射。

状态:
- `PARTIAL`, `TO_CONFIRM`

---

## 9) As-Is / To-Be / Gap / Next

- As-Is: 基础采购字段体系较完整，能覆盖需求梳理/分析/RFX主链。
- To-Be: 补齐客户新增寻源增强字段，并明确同义词映射规则。
- Gap: 供应商数量/交期时长/对标企业等字段尚未正式落表。
- Next:
  1. 先做字段映射决策（alias vs 新增字段）。
  2. 再更新 dictionary/schema/contracts/template bindings。

---

## 10) P0-2 Closure Buckets

### 已确认可直接用（Confirmed-Direct）

1. 采购目的
2. 使用场景
3. 一级品类
4. 二级品类
5. 交付地点
6. 产品/服务
7. 交付时间
8. 预算金额
9. 供应商区域
10. 候选数量

### 待客户确认（TO_CONFIRM）

1. 供应商数量（是否等同候选数量）
2. 交期时长（是否由交付时间派生）
3. 对标企业（是否进入排序因子）
4. 买家资金（是否独立于预算金额）

### 可先占位实现（Placeholder-First）

1. 供应商数量 -> alias `候选数量`
2. 交期时长 -> derived(`交付时间`, 当前日期)
3. 对标企业 -> optional 新字段占位（不阻断）

### 明确 defer（Defer）

1. 员工规模
2. 企业性质
3. 社保人数
4. 买家资金（若客户未确认独立语义）

参考:
- `docs/domain-standards/xiaocai-instance-alignment/xiaocai-field-mapping-closure-spec.md`
