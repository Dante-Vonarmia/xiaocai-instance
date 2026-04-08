# 04 Search Sourcing And Replace Rules

## 边界

- 本文定义 search、sourcing、replace 的领域规则契约。
- search 的目标是服务字段补全/替换，不是信息展示。

## 标准

### 1. Search Mapping

- 每次检索必须声明:
- `target_field`
- `query_intent`
- `query_constraints`

- 检索 evidence 结构至少包含:
- `source`
- `title`
- `snippet`
- `matched_field`
- `candidate_value`
- `confidence`

- evidence 必须可追溯到 requirement workspace 某字段。

### 2. Sourcing Rules

- 寻源输入至少包括:
- 已确认需求字段
- 品类与约束
- 合规与资质要求

- 候选输出至少包含:
- 候选主体
- 匹配理由（结构化）
- 风险提示
- 推荐强度

### 3. Replace Rules

- 字段替换分三类:
- `auto_replace_allowed`
- `recommend_only`
- `user_confirm_required`

- 替换记录必须进入 `replace_history`，至少含:
- `field_key`
- `old_value`
- `new_candidate`
- `evidence_ref`
- `decision`
- `operator`
- `timestamp`

## 验收

- 任一 search 结果均可映射到字段或任务目标。
- 任一 replace 行为可追溯 evidence 与确认动作。
- sourcing 推荐可解释，不是黑盒排序。

## 典型反例

- 用户问芯片，返回无关行业新闻。
- 检索结果无字段映射，直接塞进聊天正文。
- 替换值覆盖关键字段但没有确认与记录。

## 不做什么

- 不做无目标泛检索。
- 不做不可追溯的自动覆盖。
