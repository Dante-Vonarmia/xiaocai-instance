# CHAT-003 Intake Canonical 对接验收清单

最后更新: 2026-05-18

## 1. 目标

验证 xiaocai 在接入最新 FLARE 后，`requirement_canvas` 相关链路满足：

1. mode canonical 映射稳定；
2. 梳理态 `canvas_state` 可流式产出；
3. 历史写回与重载不丢失 `canvas_state`；
4. 不再出现旧的粗糙覆盖回复；
5. 新会话端到端体验稳定。

---

## 2. P0 手工验收（上线前必须通过）

### CHAT-003-M1：新会话梳理面板不回 0%

- 输入：
  - `我要采购一批测试服务器，请先帮我梳理采购需求并列出还缺的关键信息。`
- 预期：
  - 右侧“需求梳理”出现进度、已识别项、待补充项；
  - 加载完成后不被覆盖成 `0% / 已识别 0 项`。

### CHAT-003-M2：历史重载不丢梳理态

- 步骤：
  1. 发送 M1 输入；
  2. 切到其他会话；
  3. 再切回当前会话（或页面刷新后回到该会话）。
- 预期：
  - 右侧梳理态仍存在；
  - 进度和字段状态与发送后保持一致（允许小幅增长，不允许归零）。

### CHAT-003-M3：第二轮补充后进度上升

- 在同会话继续输入：
  - `预算 30 万，数量 20 台，交付时间 6 月底，部署在上海机房。`
- 预期：
  - progress 上升；
  - missing fields 数量下降；
  - 不出现“旧逻辑重置”。

### CHAT-003-M4：不出现粗糙覆盖问句

- 预期：
  - 不出现早期覆盖式粗糙问句（如“提问项目名称”这类替换主回答的表现）；
  - 主链路回答保留，梳理信息作为并行投影展示。

---

## 3. 自动化回归（测试驱动）

### A. 后端回归（必跑）

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents
.venv/bin/python -m pytest tests adapters/http_api/tests -q
```

通过标准：

- 全量通过（当前基线：`115 passed, 41 subtests passed`）。

### B. 前端回归（必跑）

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents
npm run type-check --prefix frame/web
npm run test --prefix frame/web
```

通过标准：

- type-check 无错误；
- vitest 全量通过（当前基线：`3 files, 7 tests passed`）。

### C. 关键链路定点（建议每次发版前补跑）

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents
.venv/bin/python -m pytest \
  adapters/http_api/tests/test_chat_core_compat.py \
  adapters/http_api/tests/test_chat_stream_projection.py \
  adapters/http_api/tests/test_sessions.py::test_append_exchange_preserves_flare_message_artifacts \
  adapters/http_api/tests/test_session_persistence_adapter.py::test_append_and_list_messages_with_flare_fields \
  -q
```

通过标准：

- 全部通过（当前基线：`9 passed`）。

---

## 4. 关键断言（供日志/接口抽检）

1. `mode=requirement_canvas` 输入后，运行态应看到 `requirement_intake`。
2. stream 事件包含 `event: canvas_state`。
3. `/sessions/{id}/messages/append` 后，`/sessions/{id}/messages` 可读回：
   - `canvas_state`
   - `plan_payload`
   - `analysis_payload`（如有）
   - `context_authority`（如有）
4. 历史读回的 `canvas_state.progress` 不为 `0`（针对该轮确实产出梳理的会话）。

---

## 5. 上线门禁（Go / No-Go）

仅当以下都满足才允许上线：

1. 手工验收 M1~M4 全部通过；
2. 自动化 A+B 全部通过；
3. 定点回归 C 通过；
4. 本地/预发数据库不存在会干扰观测的旧脏会话（必要时先清理历史再验收）。

若任一失败，状态应回到 `Blocked`，不得标记为 `Done`。

