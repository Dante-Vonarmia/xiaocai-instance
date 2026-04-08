# 02 Taxonomy And Field Model

## 边界

- 本文定义采购 taxonomy 与字段模型标准。
- 真实字段基线来源: `domain-pack/schema/procurement-field-dictionary.yaml`（Sheet3）。
- 品类基线来源: `domain-pack/category-fields/procurement-category-fields.yaml`（Sheet1）。

## 标准

### 1. Taxonomy 标准

- 三级结构: 采购负责类 -> 一级品类 -> 二级品类。
- taxonomy 以任务可执行为目标，不追求百科式穷举。
- 新品类扩展必须先走 `category-fields` 配置，不先加代码分支。

### 2. Field Model 标准

- 字段分层:
- common fields（跨品类）
- category-specific fields（品类特有）

- 每个字段必须具备以下元数据（可映射到配置项）:
- `key`
- `label`
- `type`
- `required_at_stage`
- `ask_if_missing`
- `searchable`
- `replaceable`
- `validation_rule`
- `source_of_truth`
- `display_grouping`

- 字段是 runtime 可消费结构，不是提示文案。

### 3. Category-specific Fields 标准

- 在 `category-fields` 为每个二级品类保留:
- `各品类特殊需求字段占位`
- `各品类特殊寻源要素占位`

- 当前阶段先保持占位，后续按场景逐步填充，不一次性铺满全品类。

## 验收

- `schema/workflow` 引用字段都可在字段总表命中。
- common 与 category-specific 字段边界清晰，无重复定义。
- 新增品类可通过配置完成最小可用扩展。

## 典型反例

- 字段只写“说明文字”，没有结构元数据。
- 每个品类都新增大量 service 级 if/else。
- taxonomy 与 workflow 阶段字段无映射关系。

## 不做什么

- 不发明新的 domain DSL。
- 不要求首轮完成所有品类特殊字段。
