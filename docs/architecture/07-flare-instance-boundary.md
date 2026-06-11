# FLARE 与 Instance 边界约束

## 目的

统一约束以下分层，避免后续开发重复出现“在 xiaocai 侧重写 FLARE 能力”问题：

- `FLARE`：平台能力层（像组件库）
- `xiaocai instance`：采购实例层（使用、配置、连接和沉淀业务资产，不重写内核）

当前执行口径：对 xiaocai 来说，FLARE 基本按黑盒消费，只开放稳定 contracts。domain packs 当前在 FLARE 侧完成开发、测试和 contract 验证；xiaocai 只同步和消费 FLARE 已验证状态，不在本仓库新增未经 FLARE 测试的规则、fallback、shim、alias 或 heuristic。

## 分层职责

### 1. FLARE（平台能力层）

负责提供通用能力，不承载 xiaocai 采购业务定制内容：

- 通用聊天交互框架（会话、输入区、空态、时间线、SSE 事件处理）
- 通用插槽和协议（`starterPrompts`、`uiLabels`、`modeQuickEntries` 等）
- 可复用状态管理与渲染机制
- 通用 mode / workflow / intake / readiness / canvas canonical projection
- 通用 stream / patch / event / provider normalization
- 通用 MCP / tool / connector runtime 能力（若产品需要）
- 当前 domain pack 开发、测试、contract 验证与发布态输出

### 2. xiaocai instance（采购实例层）

负责将 FLARE 已验证能力实例化到采购场景，不改 FLARE 内核行为：

- 品牌和文案（`product_name`、`brand_tag`、`uiLabels`）
- 推荐模板内容（`starterPrompts`）
- 模式入口配置（`modeQuickEntries`）
- 项目/身份上下文、API 绑定、权限范围
- FLARE 已验证 domain pack / contract 的同步、装配和消费
- 采购场景的外部数据源、MCP、供应商库、资料库连接配置
- 用户、项目、会话、资料、上传、权限等 instance 使用层能力
- 将采购上下文映射为 FLARE 已定义的输入合同，并消费 FLARE 输出投影
- xiaocai 自有数据治理、部署治理、用户环境治理

## 强制约束（MUST / MUST NOT）

### MUST

- 业务模板、业务文案、品牌信息必须放在 instance 配置层。
- 仅通过 FLARE 暴露的 props/协议接入能力。
- 当需求是“改模板内容/文案/模式项”时，只改 instance。
- xiaocai 自有数据治理、外部数据源配置必须留在 instance 使用层；domain pack 执行口径以 FLARE 已验证发布态为准。
- FLARE 已有能力必须优先复用；如果现有接口不能承接，先向 FLARE 提能力缺口。
- provider / LLM / MCP 返回必须先 normalize 到 xiaocai 或 FLARE 合同，再进入业务状态或投影。
- FLARE 行为异常时，先检查依赖版本、运行时 props、部署产物、缓存、历史 payload 和 xiaocai 侧污染。
- domain pack 变更必须来自 FLARE 已验证发布态，或作为明确的数据治理资产同步，不得在 xiaocai 侧直接新增执行规则。

### MUST NOT

- 不在 instance 侧复制或重写 FLARE 组件交互逻辑。
- 不将 xiaocai 业务文案硬编码到 FLARE 通用包。
- 不因单一 instance 诉求直接改 FLARE 默认行为（除非确认是平台级能力缺口）。
- 不在 xiaocai 本地新增 mode runtime、workflow engine、intake engine、readiness engine、canvas canonical engine。
- 不用关键词、fallback、UI 投影或 domain pack 直接改变主流程状态。
- 不把 domain pack 当作 runtime controller；domain pack 只能提供业务知识、字段、模板、策略配置。
- 不把 UI projection 当作 authoritative backend state。
- 不用 xiaocai 本地规则、fallback、shim、alias 或 heuristic 补偿 FLARE 口径不一致。
- 不在 xiaocai 侧开发未经 FLARE 测试的 domain pack 执行规则。

## 变更决策规则

先问一个问题：这是“能力”还是“内容”？

- 能力缺失（FLARE 现有 props 无法承接）：
  - 先记录为 FLARE 能力缺口；由 FLARE 补通用扩展点，再由 xiaocai 配置使用。
- 内容调整（模板文本、文案、品牌、模式项）：
  - 只改 instance 配置，不改 FLARE 内核。
- 采购资产调整（字段、品类、模板、MCP/source 配置）：
  - 当前先回 FLARE 开发、测试、验证；xiaocai 只同步 FLARE 已验证发布态或维护明确的数据治理资产，不新增运行时机制。
- 运行机制调整（mode、workflow、canvas、readiness、stream、patch、MCP runtime）：
  - 不在 xiaocai 本地开发，必须回到 FLARE。
- 运行表现不一致（FLARE 正常、xiaocai 异常）：
  - 只排查 xiaocai 运行时 props、依赖漂移、部署产物、缓存、历史 payload 或污染；不得新增 fallback/shim。

## 本仓库落点

- instance 装配入口：
  - `/Users/dantevonalcatraz/Development/procurement-agents/frame/web/src/pages/chat-page/index.tsx`
- 当前推荐模板配置示例：
  - `starterPrompts`（同文件内 `INSTANCE_STARTER_PROMPTS`）
- instance API 主边界：
  - `/Users/dantevonalcatraz/Development/procurement-agents/adapters/http_api/src/xiaocai_instance_api`
- 采购业务资产：
  - `/Users/dantevonalcatraz/Development/procurement-agents/domain-packs`
  - 当前作为 FLARE 已验证 domain pack 的同步/消费落点，不作为未经 FLARE 测试的规则开发入口。
- FLARE 包来源（外部仓库依赖）：
  - `@flare/chat-ui`
  - `@flare/chat-core`

## Domain pack opt-in 与能力展示

最新 FLARE 口径下，domain pack 不再隐式回退到 generic：

- 未显式配置 `domain_pack_domain` 时，canonical `module_prompt_registry` 应为空。
- `domain_pack_domain=generic` 只表示显式选择 generic 开放基座。
- `domain_pack_domain=xiaocai` 只表示显式选择 xiaocai 业务实例。
- xiaocai instance 转发 FLARE 请求时必须显式携带 `instance_id=xiaocai`、`domain_pack_domain=xiaocai`、`domain_pack_version=default`。
- 当前 xiaocai pack 只启用 `requirement_intake` 与 `analysis_mode`，不启用 `intelligent_sourcing`。

能力展示边界：

- backend canonical `module_prompt_registry` / capability projection 是唯一展示来源。
- 前端和 instance app 不得本地补默认 module。
- xiaocai 不得从 generic 继承 module。
- UI 不得根据 tab、mode、历史默认值猜测 capability。
- `intelligent_sourcing` 缺失表示未配置/未启用，不是前端隐藏。

## PR 自检清单

- 这次需求是否只是“内容变更”？若是，是否只改 instance？
- 是否新增了任何对 FLARE 内部实现的复制代码？
- 是否把业务词汇或业务模板放进了 FLARE 通用层？
- 是否仍然通过 props/协议完成装配？
- 是否在 xiaocai 本地新增了 runtime / workflow / canvas / readiness 机制？若是，必须停止并转 FLARE 缺口。
- 是否只是采购业务资产或连接配置？若是，应落在 domain pack / instance config / adapter 使用层。
