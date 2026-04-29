# ADR-006 Instance-owned Sourcing Connectors And Switchable Search

## Status

Accepted

## Date

2026-04-30

## Context

xiaocai 当前已经具备以下基础：

1. system settings 页面已经提供 connector 状态、启停、测试连接、优先级展示。
2. instance 侧已经区分了 `xiaocai_db`、`external_search`、`mcp_gateway` 等连接入口。
3. chat 请求进入 kernel 前，instance 侧已经会补充 `retrieval_policy` 等上下文信号。

但当前仍存在几个不应继续模糊的问题：

1. MCP 连接不应被固化为“只能有一个网关”。
2. search 入口也不应被固化为“只能有一个 external_search”。
3. 采购寻源策略属于 xiaocai 产品语义，不能下沉成 kernel 内的业务固定逻辑。
4. 页面不仅要展示连接状态，还需要逐步承接可配置能力，包括：
   - 多个 MCP 数据源
   - 多个 search 数据源
   - 启停
   - 优先级
   - 切换/路由策略

因此需要先冻结一条清晰口径，再进入后续实现补全。

## Decision

### 1. xiaocai 拥有寻源连接配置权，不把寻源策略交给 kernel

xiaocai 负责定义和持有以下内容：

- 哪些 MCP / search connector 可被当前 instance 使用
- 每个 connector 的启停状态
- connector 优先级
- connector 类型与能力标签
- 哪类采购场景优先命中哪类 connector
- search/source 切换策略
- candidate/evidence/ranking/projection 的采购语义

kernel 只负责：

- 通用 chat / tool / retrieval 执行能力
- 通用 runtime / stream / orchestration primitive
- 被 instance 提供的策略和上下文驱动执行

即：

- **xiaocai 定 policy**
- **kernel 提 mechanism**

### 2. MCP 连接默认按“多连接”模型设计

从本 ADR 起，xiaocai 的 MCP 侧能力按“**一个 instance 可以接多个 MCP connector**”作为默认设计口径。

这意味着：

- 不能把 MCP 建模成单例配置
- 不能把页面交互设计成只允许一个 MCP 来源
- 不能把后端 contract 固化成单个 `mcp_gateway` 的唯一入口语义

现有 `mcp_gateway` 可继续作为过渡 connector key 存在，但只代表当前默认项，不代表最终只能有一个。

### 3. Search 默认按“多数据源 + 可切换”模型设计

从本 ADR 起，search 侧能力按“**一个 instance 可以配置多个 search source，并允许切换/排序/路由**”作为默认设计口径。

这里的 search source 可以包括但不限于：

- external search
- MCP database-backed search
- instance 自有资料库搜索
- 后续其他供应商/知识检索源

要求：

- 页面必须允许体现多个 search source
- 后端必须允许存储多个 search source 的配置状态
- routing/policy 必须允许按场景选择 source，而不是写死单一路径

### 4. system settings 页面是配置投影层，不是策略执行层

settings 页面需要承接：

- connector 列表
- connector 状态
- healthcheck 结果
- 启停
- 优先级
- 搜索源切换和配置入口

但页面本身不是寻源执行层：

- 不在前端判断真实 sourcing policy
- 不在前端决定最终使用哪个数据源
- 不以 UI fallback 替代后端 authoritative config

页面负责 projection 和 configuration input，真实配置与执行决策仍以 instance 后端为准。

### 5. retrieval policy 由 xiaocai 生成，作为 kernel 输入

search / sourcing 执行前的 source preference、route hint、context ref、priority signal 等，归 xiaocai instance 组装。

kernel 消费这些信号，但不拥有采购业务上的 source ownership。

换言之：

- `retrieval_policy` 是 instance-owned input
- 不是 kernel-owned procurement policy

## Non-Goals

本 ADR 不在当前阶段定义：

1. 最终 connector schema 完整字段集。
2. 最终 MCP connector discovery 协议。
3. search routing DSL 最终语法。
4. 每个 procurement scenario 的最终 source-selection matrix。
5. UI 最终交互细节和视觉方案。

## Consequences

正向影响：

1. 固定“多 MCP、多 search source、可切换”的演进方向。
2. 固定“寻源策略归 xiaocai，执行能力归 kernel”的边界。
3. 避免后续把 connector / search 错误固化成单例模型。
4. 为 settings 页面补配置能力提供明确依据。

代价：

1. 当前 `mcp_gateway` / `external_search` 的单项展示模型后续需要升级。
2. 后端 connector 存储与 contract 需要从固定 key 模型逐步演进到 registry/list 模型。
3. retrieval policy 组装逻辑需要从当前基础权重信号继续补到可路由、可切换的策略层。

## Implementation Notes

后续补全时，至少要覆盖三层：

1. **Config Layer**
   - connector registry
   - connector type
   - enabled / priority / routing metadata

2. **Policy Layer**
   - source selection
   - search switching
   - scenario-to-connector routing

3. **Projection Layer**
   - settings 页面展示与编辑入口
   - status / health / priority / selected source 展示

## Extraction Guidance

本 ADR 明确以下提炼口径：

### 1. 当前阶段默认留在 xiaocai instance

以下能力当前默认归属 xiaocai instance，不上提到 FLARE：

- connector registry 的产品配置语义
- search source 的默认值、fallback、优先级、场景路由
- `intelligent_sourcing` 的 source selection 策略
- settings 页面上的 connector / search source 配置入口
- procurement sourcing 的 evidence / ranking / projection 语义

原因：

1. 这些能力当前仍带有明显的 procurement / instance / UI 语义。
2. 这些能力当前仍直接服务 xiaocai 的产品闭环，而不是平台通用闭环。
3. 当前 contract、字段和页面交互仍处于演进中，尚未达到平台级冻结条件。

### 2. 未来可以提炼的仅是通用 capability

未来若要上提到 FLARE，只允许提炼以下“去业务化”的通用能力：

- 通用 connector registry primitive
- 通用 connector health / status contract
- 通用 source selection / fallback carrier
- 通用 retrieval policy routing primitive

明确不提炼：

- procurement-specific source routing
- `intelligent_sourcing` 命名与模式语义
- supplier sourcing 策略
- xiaocai settings / workbench 的页面投影语义

### 3. 提炼前置条件

只有同时满足以下条件，才应考虑把能力从 xiaocai 上提到 FLARE：

1. 至少两个 instance 存在真实复用需求。
2. 能力本身不再依赖采购业务词汇。
3. 不再依赖 xiaocai settings 页面交互语义。
4. 输入输出 contract 已稳定，可脱离 xiaocai 单独解释。
5. 上提后不会把 FLARE 变成产品层或行业层实现。

若任一条件不满足，则继续保留在 xiaocai instance。

### 4. 当前执行策略：先在 xiaocai 完成功能，再决定是否迁移

本 ADR 进一步冻结当前执行顺序：

1. 先在 xiaocai instance 内完成 connector registry、search source policy、settings 配置入口、runtime routing hint、以及 sourcing 相关产品闭环。
2. 当前阶段不以“能否立即迁移到 FLARE”作为实现前置条件。
3. 只要能力仍主要服务 xiaocai 的 procurement 产品流程，就允许继续在 xiaocai 侧补全。
4. 等到 xiaocai 内部能力稳定、跨 instance 复用需求明确后，再单独发起提炼评估与迁移设计。

这意味着：

- **当前优先级是把 xiaocai 功能做完整**
- **迁移到 FLARE 是后续可选动作，不是本阶段阻塞项**
- **不得为了“提前抽象”牺牲当前产品闭环与交付效率**

## Related

- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-004-instance-api-execution-baseline.md`
- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-005-collaboration-permission-layering.md`
- `/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/07-flare-instance-boundary.md`
