# ADR-007 Domain Prior Resolver And Soft-bias Execution

## Status

Proposed

## Date

2026-04-30

## Context

xiaocai 当前已经具备一批采购领域资产：

1. 字段总表：`domain-packs/schema/procurement-field-dictionary.yaml`
2. 品类目录：`domain-packs/category-fields/procurement-category-fields.yaml`
3. 分析 / RFX 模板：`domain-packs/contracts/procurement-analysis-rfx-templates.yaml`
4. 模板推荐规则：`domain-packs/shared/rules/template_recommendation_rules.yaml`
5. 工作流节点定义：`domain-packs/workflows/procurement-workflow-nodes.yaml`

这些资产已经说明 xiaocai 的目标不是“通用聊天”，而是“采购领域下的产品级 orchestration”。

但当前运行态仍存在几个问题：

1. 采购运行逻辑仍有半写死成分，尤其体现在：
   - `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/extractor.py`
   - `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/constants.py`
2. 领域资产已经存在，但尚未形成稳定的运行时执行闭环。
3. plan mode 当前主要承担上下文增强、提示组织、输入整理，不应被误当作 authoritative domain rule owner。
4. 团队不希望把小采做成“固定问死问题”的表单式代理，而是希望：
   - 保留大模型的自然理解能力；
   - 同时让采购领域资产作为更高权重的先验（prior）；
   - 使模型输出更靠近 xiaocai 定义的目标空间。

因此需要冻结一条明确口径：

- **LLM 负责生成候选理解**
- **xiaocai domain pack 负责提供 hard gate、prior、scoring、re-ranking**
- **plan mode 负责交互辅助与上下文增强**

## Decision

### 1. 采用 “LLM Candidate + Domain Prior Resolver” 执行模型

xiaocai 不把采购领域逻辑交给纯 prompt 或纯模型自由生成。

固定采用如下执行顺序：

1. LLM 生成候选理解
2. domain resolver 加载 procurement domain assets
3. hard gate 校验
4. soft bias / scoring / re-ranking
5. 低置信度时触发必要追问
6. 将最终结果投影到 workbench / response contract

即：

- **模型给候选**
- **domain pack 给先验**
- **resolver 给最终运行时判断**

### 2. 采购领域资产作为 prior，不作为“死板问卷”

xiaocai 不追求把所有需求变成固定问卷流。

采购领域资产的职责是：

1. 提供标准字段空间
2. 提供标准品类空间
3. 提供模板候选集合
4. 提供场景化推荐权重
5. 提供字段依赖和阻断条件
6. 提供寻源与分析的约束和排序依据

这些资产用于：

- 提升与领域资产一致的候选分数
- 降低与领域资产冲突的候选分数
- 在关键字段缺失时阻断下一阶段

而不是用于：

- 强迫用户按固定表单回答全部字段
- 让 UI 或 prompt 伪装成 authoritative workflow

### 3. hard gate 与 soft bias 必须分层

#### hard gate

用于决定某候选、某模板、某动作是否允许进入下一步。

示例：

1. 关键字段缺失时禁止进入需求分析 / RFX / 智能寻源
2. 模板依赖字段不足时禁止推荐该模板
3. category 与字段组合明显冲突时禁止直接确认

#### soft bias

用于对允许集合内的候选做排序增强。

示例：

1. category 命中标准品类树或别名时加权
2. 模板在当前场景下有更高基础权重时加权
3. 字段组合更符合当前场景时加权
4. 与历史案例、知识库或检索结果更接近时加权

结论：

- **hard gate 决定能不能**
- **soft bias 决定优不优先**

### 4. procurement-base 与 tenant overlay 分层

冻结三层领域结构：

1. **procurement-base**
   - 通用采购字段、品类、模板、规则、默认权重
   - 是 xiaocai 采购产品的标准基线

2. **tenant / app overlay**
   - xiaocai A / xiaocai B / 其他实例在基线上的差异覆盖
   - 可覆盖品类、字段、模板、权重、别名、场景策略
   - 不复制完整 procurement-base

3. **runtime resolved context**
   - 由 resolver 合并 base + overlay 后生成
   - 供 chat / plan mode / sourcing / analysis 消费

overlay 允许定制：

- 品类增删
- 品类别名
- 特殊字段
- 模板候选
- 模板权重
- 场景化规则

overlay 不允许改写：

- FLARE kernel / runtime
- transport / SSE / session primitive
- xiaocai authoritative workflow contract 边界

### 5. plan mode 定位为交互辅助层，不是领域真规则层

plan mode 可以继续作为 xiaocai 亮点能力，但职责冻结为：

1. 组织下一步追问
2. 帮助补充上下文
3. 帮助用户理解缺失项和推荐动作
4. 生成更高质量的 prompt / context input

plan mode 不拥有以下真状态：

1. required fields 定义权
2. category truth 定义权
3. readiness / gate 判定权
4. 模板允许性定义权

plan mode 必须消费 resolver 的结果，而不是自行发明规则。

### 6. 当前阶段不以向量数据库作为前置条件

当前优先建设顺序不是 vector DB，而是：

1. domain asset compiler / loader
2. authoritative resolver
3. hard gate + scoring + re-ranking
4. runtime contract 注入

向量检索仅作为后续增强层，适用于：

1. 模糊 category 召回
2. 字段语义近似匹配
3. 模板软排序增强
4. 历史案例相似性参考

明确禁止：

- 让向量召回直接成为 authoritative state
- 用 embedding similarity 替代 hard gate

即：

- **vector retrieval = candidate recall / ranking enhancement**
- **resolver = authoritative decision owner**

### 7. 运行时必须引入显式 resolver / scorer

xiaocai 运行时需要新增显式 owner，负责：

1. category candidate scoring
2. field completeness scoring
3. template candidate scoring
4. hard gate blocking
5. low-confidence clarification triggering
6. resolved domain context projection

其输入应至少包括：

1. user message
2. session history
3. current stage / mode
4. domain-pack base assets
5. tenant / app overlays
6. retrieval / knowledge refs（若存在）

其输出应至少包括：

1. resolved category path
2. required fields
3. recommended fields
4. missing fields with priority
5. allowed actions
6. blocked actions and reasons
7. template candidates with scores
8. sourcing / analysis hints
9. prompt hints for downstream model call

## Non-Goals

本 ADR 不在当前阶段定义：

1. 最终 YAML schema 完整字段细节
2. 向量数据库选型（Qdrant / pgvector / Milvus 等）
3. 最终 scoring 数学公式的精确参数
4. 最终 UI/workbench 展示形态
5. 是否把该能力未来上提到 FLARE

## Consequences

正向影响：

1. 明确“领域真规则”与“plan mode 辅助提示”的边界。
2. 避免继续在 extractor/constants/prompt 中扩散采购硬编码。
3. 为 xiaocai A / xiaocai B 提供 base + overlay 的可扩展路径。
4. 让大模型输出更接近采购目标空间，同时保留自然语言理解弹性。
5. 为后续向量增强留出清晰接入点，而不污染 authoritative state。

代价：

1. 需要新增 resolver / scorer / loader contract 层。
2. 需要逐步替换现有运行时中的采购硬编码。
3. 需要把 Excel / YAML 资产进一步整理成稳定可执行格式。
4. migration 期间可能需要保留双路径（旧 fallback + 新 resolver）。

## Implementation Notes

### 1. 优先级顺序

先做：

1. procurement-base asset 收口
2. tenant/app overlay merge 机制
3. resolver contract
4. hard gate / soft bias scoring
5. chat runtime 接线

后做：

6. vector recall enhancement
7. historical case similarity
8. 更复杂的 graph / weight tuning

### 2. 推荐文件边界

建议后续至少形成以下边界：

1. `domain_packs/contracts.py`
   - resolved domain context / scoring input-output contract

2. `domain_packs/loader.py`
   - 只负责加载 base pack + overlay

3. `domain_packs/resolver.py`
   - 只负责 category/field/template resolution

4. `domain_packs/scorer.py`
   - 只负责 soft bias scoring

5. `chat/...`
   - 只消费 resolved context，不定义采购真规则

### 3. 当前仓内替换目标

后续实现时，优先收敛以下位置的采购写死逻辑：

1. `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/extractor.py`
2. `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/constants.py`
3. `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/contract_loader.py`

目标不是一次性删除 fallback，
而是先把 authoritative path 明确到 resolver，再逐步缩小 fallback 的职责。

## Migration Rule

迁移顺序固定为：

1. 先把 procurement-base 资产整理成可稳定加载的主源
2. 再引入 overlay 合并
3. 再让 resolver 产出 authoritative resolved context
4. 最后把 chat / plan mode / template selection 全部切到 resolver 输出

任何阶段都不得：

1. 让 plan mode 反向成为领域真状态 owner
2. 让 vector recall 直接覆盖 hard gate
3. 把 procurement-specific policy 下沉到 FLARE kernel

## Extraction Guidance

当前阶段默认保留在 xiaocai instance 内的能力：

1. procurement-base domain assets
2. tenant/app overlay semantics
3. template recommendation policy
4. category / field / template resolver
5. sourcing / analysis scoring semantics
6. plan mode 的 projection / interaction semantics

未来仅在满足以下前提时，才考虑向 FLARE 提炼通用 capability：

1. 至少两个 instance 有真实复用需求
2. 已剥离采购业务词汇
3. 输入输出 contract 稳定
4. 不再依赖 xiaocai workbench / plan mode 语义

若任一条件不满足，则继续保留在 xiaocai instance。
