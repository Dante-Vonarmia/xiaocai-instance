# xiaocai instance canonical contract（锁版）

> 当前 domain-pack source/path 以 `docs/contracts/xiaocai-domain-pack-source-contract.md` 为准。legacy domain-pack 目录已删除，本文所有主链路字段与品类引用均指向 `domain-packs/xiaocai/`。

## 1. 目标

统一 instance 内部 authoritative source 到 canonical state，同时对外兼容当前 pending contract 输出。

## 2. Canonical State（最小）

1. `project_id`
2. `session_id`
3. `current_flow`
4. `current_stage`
5. `candidate_fields`
6. `confirmed_fields`
7. `rejected_candidates`
8. `field_history`
9. `missing_fields`（required/recommended/optional，derived）
10. `readiness`（derived）
11. `next_actions`（derived）
12. `active_work_item`
13. `completed_work_items`
14. `warnings/errors`

## 3. Canonical Field Candidate Payload（最小）

大模型、规则抽取、OCR、检索和附件解析输出都必须先进入 candidate 层，不得直接写入 `confirmed_fields`。

1. `field_key`：必须命中字段字典 canonical 字段，或通过 `field_aliases` 映射到 canonical 字段。
2. `raw_field_key`：模型或外部输入原始字段名。
3. `raw_value`：模型或外部输入原始值。
4. `normalized_value`：经过字段类型、别名、单位、格式和品类目录归一化后的值。
5. `source`：`user_explicit` / `model_inferred` / `rule_extracted` / `retrieval_evidence` / `domain_default`。
6. `confidence`：`0.0` 到 `1.0`。
7. `evidence`：原文片段、附件引用、检索结果或规则命中说明。
8. `normalization_status`：`accepted` / `needs_confirmation` / `rejected`。
9. `rejection_reason`：仅当 rejected 时填写。

## 4. Candidate -> Confirmed 晋级规则

1. `confirmed_fields` 只保存已通过 canonical 校验的权威字段。
2. 字段名必须存在于 `domain-packs/xiaocai/fields.yaml#field_definitions`。
3. `一级品类` / `二级品类` 必须命中 `domain-packs/xiaocai/taxonomy.yaml#procurement_categories`。
4. `model_inferred` 默认只能进入 `candidate_fields`，不能直接晋级为 confirmed。
5. `user_explicit` 可在字段名和值均通过 canonical 校验后晋级。
6. `rule_extracted` 可在有明确原文 evidence 且规则不发明业务值时晋级。
7. `domain_default` 只能作为候选或展示建议，不能作为用户已确认值。
8. split / alias / derived 字段晋级时必须写入 `field_history`。

## 5. Canonical Question Payload（最小）

1. `question_id`
2. `field_key`
3. `title`
4. `prompt`
5. `helper_text`
6. `options`
7. `allow_custom_input`
8. `input_hint`
9. `why_this_matters`
10. `source_stage`
11. `step_index`
12. `step_total`

`options` 只能来自字段字典、品类目录、配置中心或 FLARE canonical question planner，不允许由 adapter/orchestration Python 常量硬编码业务选项。

## 6. 对外映射（兼容 current API）

1. `pending_contract.question_payload` 作为标准问题对象。
2. 保留 `pending_contract.question/current_question` 仅作镜像兼容，不作 authoritative source。
3. `pending_contract.missing_fields` 对应 canonical `missing_fields.required`。
4. `pending_contract.gate` 对应 canonical `readiness`。
5. `pending_contract.next_actions` 由 canonical 派生输出。
6. `pending_contract.fields` 若存在，只能来自 canonical `confirmed_fields` 的兼容投影。
7. `pending_contract.candidates` 若存在，只能来自 canonical `candidate_fields` 的兼容投影。

## 7. 禁止项

1. 禁止 router 或 UI 反推并补写 `question_payload`。
2. 禁止 `service` 通过 intent if/else 决定主流程。
3. 禁止把 `pending_contract` 作为临时字符串容器而非结构契约。
4. 禁止将大模型输出、检索输出或规则猜测直接写入 `confirmed_fields`。
5. 禁止使用 `"已由用户给出（会话上下文）"` 这类伪值占位。
6. 禁止在 runtime 代码中硬编码采购业务选项、品类路径或字段问法。
