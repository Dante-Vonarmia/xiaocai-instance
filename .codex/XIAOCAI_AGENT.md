# XIAOCAI Project Codex Agent Rules

## A. xiaocai 项目定性

- xiaocai 是构建在 FLARE 之上的产品级应用 / orchestration repo。
- xiaocai 不是另一个通用内核。
- xiaocai 不是只有少量字段规则的薄 instance。
- xiaocai 承接真实产品流程：需求梳理、字段收集、工作台状态、需求分析、寻源链路、资产生成、结果投影。
- xiaocai 是采购场景下真正面向用户和产品闭环的主应用 repo。
- 截图、工作台链路、数据契约、状态推进、用户可见流程语义，主要属于 xiaocai 层。

## B. xiaocai 与 FLARE 的真实边界

### 1) FLARE 负责什么

- 通用 kernel/runtime。
- session / transport / stream / patch / event 基础机制。
- 通用 canonical protocol/primitives。
- 通用 mode orchestration 基座（若已存在）。
- 脱离具体行业的基础能力边界。
- 可被多个实例复用的稳定平台能力。

### 2) xiaocai 负责什么

- 产品级 orchestration。
- procurement app semantics。
- requirement intake 的产品闭环。
- 工作台 / workbench 语义。
- 用户可见的 question / next action / readiness / field progression 投影逻辑。
- requirement analysis 应用链路。
- sourcing / retrieval 应用链路。
- artifact / asset generation 应用链路。
- procurement-specific 字段体系、模板语义、分析口径、生成策略。
- 将 FLARE 的通用底座收束成真实可用产品。

### 3) 边界纪律

- xiaocai 可承接产品级 orchestration，但 MUST NOT 反向复制或篡改 FLARE kernel。
- xiaocai MUST NOT 在本地新增底层 runtime / transport / session engine。
- FLARE 提供平台级通用能力；xiaocai 负责产品级收口，不重写平台职责。
- 若已有 FLARE contract freeze / canonical primitive，xiaocai MUST 基于其扩展或投影，不得破坏。
- xiaocai 可定义产品级 data/workbench/app flow contract，但必须与 FLARE canonical contract 分层。
- MUST 区分平台底层真状态与产品展示/工作台投影状态。

## C. 全局工程哲学

- stable core, replaceable edges
- normalize input, standardize output
- one-way dependency direction
- one file, one role
- small modules over convenience monoliths
- composition over inheritance
- no speculative abstraction
- explicit contracts over loose dict passing
- xiaocai 的核心价值包括 procurement domain rules 与产品编排能力两部分。
- 产品编排必须显式、模块化、可检查。
- 禁止把产品编排散落在前端、prompt、fallback、route、giant service 的隐式逻辑中。

## D. 强制架构分层

### 1) transport / api

- 允许：接收输入、基础校验、调用应用层、返回响应。
- 禁止：复杂产品编排。
- 禁止：采购主规则。
- 禁止：拼装大段 prompt。
- 禁止：将 route/resolver 作为总调度中心。

### 2) product orchestration / application / workflow

- 这是 xiaocai 核心层之一。
- 负责 intake -> readiness -> analysis -> sourcing -> artifact 主闭环。
- 负责工作台状态推进、阶段切换、下一步动作组织、产品级结果收口。
- 可协调 domain capability 与 FLARE runtime primitives。
- 禁止：provider SDK 细节。
- 禁止：ORM/SQL 细节。
- 禁止：giant orchestrator / giant service file。
- 要求：按 workflow/stage/bounded concern 拆分。

### 3) domain capability / procurement semantics

- 负责字段体系、缺失字段规则、分析口径、模板映射、寻源判断、默认值策略、资产生成语义。
- 这是 xiaocai 最可迁移的领域核心之一。
- 禁止：依赖 transport/framework。
- 禁止：直接依赖 provider SDK。
- 禁止：混入 UI/workbench 细节。

### 4) contracts / app contracts / patch / event / schema / projection

- xiaocai 可定义产品级 contract、工作台投影 contract、结果结构 contract。
- 负责 DTO、view model、error schema、app-level event/presentation contract。
- 要求：显式、稳定、可检查。
- 禁止：loose dict 漂流。
- 必须区分 canonical contract 与产品投影 contract。
- 禁止把展示投影字段当成 authoritative state。

### 5) infra / adapters / providers / persistence

- 负责 LLM/OCR/存储/检索/数据库/缓存/第三方 provider/search 集成。
- 禁止：采购业务规则。
- 禁止：provider 返回直接成为 domain truth。
- 要求：所有外部调用经 adapter/provider 边界隔离。

### 6) web / workbench / presentation

- 负责展示、交互、timeline/checkpoint/workbench 体验。
- 可承接产品交互语义。
- 禁止：发明 authoritative backend state。
- 禁止：用 UI fallback 取代真实 workflow。
- 禁止：把主流程编排埋入组件逻辑。

## E. xiaocai 专属硬规则

### 1) 核心闭环不是“聊天”

- requirement intake
- structured field collection
- field confirmation / missing field tracking
- readiness / completeness judgment
- requirement analysis
- intelligent sourcing / retrieval
- artifact / asset generation
- workbench projection / user-visible orchestration result

### 2) 产品编排必须显式存在

- 禁止假设能力会从 prompt 自然长出。
- 禁止把复杂编排散落到前端 fallback、route、临时 helper、prompt if/else。
- 必须由明确的 application/workflow/orchestration 层承接主流程。

### 3) requirement intake 是第一等能力

- 必须表达 confirmed fields、missing fields、current question、next actions、readiness 显式状态。
- 必须与 workbench 与用户可见流程语义对齐。
- 若已有 contract freeze/canonical field 定义，必须服从，不得改义。

### 4) workbench projection 与底层真状态分离

- 阶段、区块、checkpoint、timeline、提示、推荐动作可作为产品投影。
- 产品投影不等于底层 authoritative state。
- 禁止将 UI projection 反向作为后端真状态来源。

### 5) procurement 语义归属 xiaocai

- 字段定义、模板语义、预算/数量/规格/场景/交付规则、分析口径、寻源判断、资产生成映射，必须位于 xiaocai domain capability/application 边界。
- 不得写入 FLARE kernel。

### 6) workflow 必须显式

- 多步骤链路必须走明确 workflow/state progression。
- 禁止把主流程藏进 if/else、UI fallback、prompt 拼接。
- analysis/sourcing/artifact 进入条件必须有明确 owner。
- 前端不得猜测 ready 状态。

### 7) AI / LLM / OCR

- prompts 必须集中治理。
- provider-specific logic 不得扩散。
- model output 必须先 normalize，再进入产品逻辑或领域逻辑。
- OCR/LLM/search 结果必须先转换为 xiaocai contract。
- AI workflow 必须产出显式 result/event/patch/projection input。
- failure/retry/partial state 必须可表示。

### 8) 不得伪装成 FLARE kernel

- 禁止在 xiaocai 复制 runtime 引擎。
- 禁止在 xiaocai 复制通用 stream/transport/session 基础设施。
- 需要平台能力时通过 FLARE 边界接入。
- 产品级 orchestration 和 app flow 可在 xiaocai 明确承接，不错误下沉回 FLARE。

## F. 文件纪律

- preferred file size under 200 lines
- warning threshold at 300 lines
- hard split threshold at 350 lines
- if a file would exceed 350 lines, split first, continue second
- 禁止 god file / god service / god utils / catch-all helper
- 禁止模糊文件名：`utils/common/helper/manager/service`，除非职责单一且命名可自证
- 一个文件不得混 transport + orchestration + persistence + provider integration
- 一个文件不得同时承载 intake + analysis + sourcing + artifact generation 多主职责
- workbench projection / app contract / procurement semantics / provider integration 应尽量分文件分层

## G. 变更纪律

- 禁止 coding before planning file changes。
- 修改前必须列出将创建/修改的文件及职责。
- 大文件追加逻辑前先拆分。
- diff 必须小、职责清晰、可 review。
- 禁止把结构性重构藏在功能开发里。
- 禁止 drive-by cleanup。
- 禁止把 unrelated 逻辑顺手塞进同一文件。

## H. AI / Agent 项目专项纪律

- prompts 必须集中治理，不得遍地散落。
- provider output 不得直接成为产品真状态或领域真状态。
- 产品真状态与展示投影必须分清。
- 任一步骤失败后，系统仍需可表示当前状态，不得丢失上下文。
- intake / analysis / sourcing / artifact / workbench projection 的状态 owner 必须清晰。
- 用户可见输出与系统内部 canonical state 必须分清。

## I. xiaocai 最终执行标准

在 xiaocai 中，好的代码必须体现：产品级 orchestration 显式存在但不伪装成 kernel，采购领域核心可迁移，输入先标准化，输出有明确 contract，底层真状态与产品投影分层，状态推进显式，边界清晰，小文件，低耦合，低惊讶度，前端不发明后端真状态，外部 provider 可替换。
