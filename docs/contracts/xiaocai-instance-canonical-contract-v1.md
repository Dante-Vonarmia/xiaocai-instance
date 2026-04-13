# xiaocai instance canonical contract v1（锁版）

## 1. 目标

统一 instance 内部 authoritative source 到 canonical state，同时对外兼容当前 pending contract 输出。

## 2. Canonical State（最小）

1. `project_id`
2. `session_id`
3. `current_flow`
4. `current_stage`
5. `confirmed_fields`
6. `field_history`
7. `missing_fields`（required/recommended/optional，derived）
8. `readiness`（derived）
9. `next_actions`（derived）
10. `active_work_item`
11. `completed_work_items`
12. `warnings/errors`

## 3. Canonical Question Payload（最小）

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

## 4. 对外映射（兼容 current API）

1. `pending_contract.question_payload` 作为标准问题对象。
2. 保留 `pending_contract.question/current_question` 仅作镜像兼容，不作 authoritative source。
3. `pending_contract.missing_fields` 对应 canonical `missing_fields.required`。
4. `pending_contract.gate` 对应 canonical `readiness`。
5. `pending_contract.next_actions` 由 canonical 派生输出。

## 5. 禁止项

1. 禁止 router 或 UI 反推并补写 `question_payload`。
2. 禁止 `service` 通过 intent if/else 决定主流程。
3. 禁止把 `pending_contract` 作为临时字符串容器而非结构契约。
