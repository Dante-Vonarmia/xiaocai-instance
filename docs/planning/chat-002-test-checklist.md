# CHAT-002 测试先行清单（instance 轻量化）

最后更新: 2026-05-18

## 1. 目标

在不新增 instance 侧业务编排的前提下，先用回归测试锁定以下问题：

1. `mode=auto` 不应粘住历史 intake mode。
2. 非显式梳理意图不应出现“需求梳理草稿”投影泄漏。
3. 普通自然对话不应被缺字段策略阻断。
4. 局部失败应降级为“可继续对话”（不强阻断）。
5. 先测试后实现，每条修复必须有对应用例证据。

---

## 2. 用例清单（先写测试）

### CHAT-002-T1：auto 不继承历史 intake 粘性

- 目的：验证同一 session 历史是 `requirement_intake` 时，当前请求显式 `mode=auto` 不被强行拉回 intake。
- 建议位置：`adapters/http_api/tests/test_chat.py`（或新增 `test_chat_mode_regression.py`）
- 预期：
  1. kernel 请求 context 中 `mode` 为 `auto`（或空值按约定）；
  2. 不因 session.mode= intake 自动切回 intake；
  3. 返回不附带 intake 专属 pending/projection 字段。

### CHAT-002-T2：非显式梳理意图不生成需求梳理投影

- 目的：验证普通问题（如“为什么会自己冒出来”）在 `auto` 下不触发 `canvas_state` 的梳理草稿。
- 建议位置：`adapters/http_api/tests/test_chat_stream_projection.py`
- 预期：
  1. SSE 流中不出现 `event: canvas_state`（intake draft）；
  2. 文本中不出现 `# 需求梳理草稿`；
  3. 不出现 `event: text.replace` 的梳理追问覆盖。

### CHAT-002-T3：自然对话不被缺字段策略阻断

- 目的：验证普通问答场景下，不因 `clarification_policy` / `confidence_policy` 直接走 blocked 提示。
- 建议位置：`adapters/http_api/tests/test_chat_prior_context.py`
- 预期：
  1. `pending_contract` 不被伪造；
  2. 正常返回自然语言答复；
  3. metadata 不出现 intake 强绑定字段（除非显式 intake）。

### CHAT-002-T4：局部失败降级为可继续对话

- 目的：验证 kernel 局部异常时不直接“消息发送失败/生成失败”硬阻断。
- 建议位置：`adapters/http_api/tests/test_chat.py`
- 预期：
  1. `/chat/stream` 出错时仍输出可消费终态事件（done/complete 或明确降级 content）；
  2. `/chat/run` 出错场景有可恢复提示，不要求用户重建会话；
  3. 不出现仅技术错误且无可执行下一步的回复。

### CHAT-002-T5：显式 intake 仍保持原能力

- 目的：防止修复过程中误伤梳理闭环。
- 建议位置：复用
  - `adapters/http_api/tests/test_chat_workbench_projection.py`
  - `adapters/http_api/tests/test_chat_stream_projection.py`
- 预期：
  1. 显式 `mode=requirement_canvas` / `requirement_intake` 时，原有梳理投影仍可用；
  2. native pending / canvas_state 优先级不被破坏。

---

## 3. 执行命令（验收门）

> 先补测试，再允许改实现。

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents
python3 -m pytest \
  adapters/http_api/tests/test_chat.py \
  adapters/http_api/tests/test_chat_prior_context.py \
  adapters/http_api/tests/test_chat_stream_projection.py \
  adapters/http_api/tests/test_chat_workbench_projection.py -q
```

可选增量命令（按新增测试文件名调整）：

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents
python3 -m pytest adapters/http_api/tests/test_chat_mode_regression.py -q
```

---

## 4. 证据留痕要求

每次提交 `CHAT-002` 子修复都必须附：

1. 修改文件列表（最小集）。
2. 对应测试用例 ID（T1~T5）。
3. pytest 命令与通过结果。
4. 若有行为变化，更新 `docs/planning/README.md` 中 `CHAT-002` 状态。

---

## 5. 边界约束

1. 不在 instance 新增 workflow engine。
2. 不在 router 增加新的产品编排分支。
3. 不在 UI 发明 authoritative state。
4. 只做“模式粘性收口 + 投影泄漏收口 + 降级兜底”最小修复。
