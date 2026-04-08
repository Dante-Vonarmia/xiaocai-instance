# FLARE 与 Instance 边界约束

## 目的

统一约束以下分层，避免后续开发重复出现“在 instance 侧重写 FLARE 能力”问题：

- `FLARE`：平台能力层（像组件库）
- `xiaocai instance`：业务装配层（只配置，不重写内核）

## 分层职责

### 1. FLARE（平台能力层）

负责提供通用能力，不承载 xiaocai 业务定制内容：

- 通用聊天交互框架（会话、输入区、空态、时间线、SSE 事件处理）
- 通用插槽和协议（`starterPrompts`、`uiLabels`、`modeQuickEntries` 等）
- 可复用状态管理与渲染机制

### 2. xiaocai instance（业务装配层）

负责装配 xiaocai 业务内容，不改 FLARE 内核行为：

- 品牌和文案（`product_name`、`brand_tag`、`uiLabels`）
- 推荐模板内容（`starterPrompts`）
- 模式入口配置（`modeQuickEntries`）
- 项目/身份上下文、API 绑定、权限范围

## 强制约束（MUST / MUST NOT）

### MUST

- 业务模板、业务文案、品牌信息必须放在 instance 配置层。
- 仅通过 FLARE 暴露的 props/协议接入能力。
- 当需求是“改模板内容/文案/模式项”时，只改 instance。

### MUST NOT

- 不在 instance 侧复制或重写 FLARE 组件交互逻辑。
- 不将 xiaocai 业务文案硬编码到 FLARE 通用包。
- 不因单一 instance 诉求直接改 FLARE 默认行为（除非确认是平台级能力缺口）。

## 变更决策规则

先问一个问题：这是“能力”还是“内容”？

- 能力缺失（FLARE 现有 props 无法承接）：
  - 先补 FLARE 通用扩展点，再由 instance 配置使用。
- 内容调整（模板文本、文案、品牌、模式项）：
  - 只改 instance 配置，不改 FLARE 内核。

## 本仓库落点

- instance 装配入口：
  - [ChatPage.tsx](/Users/dantevonalcatraz/Development/procurement-agents/frame/web/src/pages/ChatPage.tsx)
- 当前推荐模板配置示例：
  - `starterPrompts`（同文件内 `INSTANCE_STARTER_PROMPTS`）
- FLARE 包来源（外部仓库依赖）：
  - `@flare/chat-ui`
  - `@flare/chat-core`

## PR 自检清单

- 这次需求是否只是“内容变更”？若是，是否只改 instance？
- 是否新增了任何对 FLARE 内部实现的复制代码？
- 是否把业务词汇或业务模板放进了 FLARE 通用层？
- 是否仍然通过 props/协议完成装配？
