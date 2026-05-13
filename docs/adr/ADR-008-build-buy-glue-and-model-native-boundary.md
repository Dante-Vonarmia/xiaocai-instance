# ADR-008 Build / Buy / Glue And Model-native Boundary

## Status

Accepted

## Date

2026-05-09

## Context

xiaocai 的核心产品闭环已经接近成型：

1. 需求梳理、字段确认、缺失字段推进。
2. 采购领域分析、寻源、证据、产物投影。
3. workbench 中的用户可见流程语义。
4. FLARE / AgentRuntime 作为通用基座，提供运行时、模型、stream、tool、connector 等平台能力。

但随着大模型能力快速提升，一些原本可能通过自研规则、tracker、scorer、extractor 深做的能力，未来可能直接由更强模型提供更好效果。

典型例子包括：

1. 对话追踪。
2. 自然语言字段抽取。
3. 意图理解。
4. 上下文整理。
5. 初步问题生成。
6. 候选模板或候选动作建议。

因此需要冻结一条新的执行口径：

- xiaocai 仍必须拥有完整产品能力和交付闭环。
- FLARE / AgentRuntime 仍应逐步沉淀通用可复用能力。
- 当前交付不应因为等待自研通用能力而变慢。
- 对模型原生能力，应优先采用 Glue-first 策略，同时保留 contract、adapter、eval 和替换边界。

## Decision

### 1. 采用 Build / Buy / Glue 三分法作为默认工程判断

每个新能力进入实现前，必须先判断其归属：

| 类型 | 定义 | 默认动作 |
|---|---|---|
| Build | xiaocai 或 FLARE 必须自有的产品真状态、业务策略、平台通用能力 | 自研并建立稳定 contract |
| Buy | 非差异化基础设施或成熟第三方能力 | 购买、托管、接入，不自研 |
| Glue | 外部能力或模型能力与 xiaocai/FLARE contract 的连接层 | adapter + normalize + trace + eval |

Build / Buy / Glue 不是永久标签。能力可以先 Glue，等稳定后再 Build 或上提到 FLARE。

### 2. 区分“现在不 Build”和“最终不拥有”

对于完整产品和 AgentRuntime 基座，以下能力长期应有自有边界：

1. tracker / memory / state progression capability。
2. tool routing / source routing capability。
3. model provider routing / fallback capability。
4. contract-based output normalization。
5. eval / trace / audit capability。
6. domain pack / industry pack execution hook。

但当前阶段不要求全部深度自研。

执行口径：

1. 当前交付优先 Glue 到可用能力。
2. 自有边界先体现为 contract、adapter、trace、eval。
3. 只有当能力稳定且跨 instance 复用明确时，再 Build 到 FLARE / AgentRuntime。
4. 不为尚未稳定的模型推理能力提前写复杂规则内核。

### 3. Model-native 能力默认 Glue-first

如果一个能力主要由大模型的自然语言理解、推理、总结、规划能力决定，默认归为 Model-native capability。

Model-native 能力当前默认不深做自研规则系统，只保留：

1. 输入 contract。
2. 模型调用 adapter。
3. 输出 schema。
4. normalize / validation。
5. confidence / reason / trace。
6. eval case。
7. fallback 策略。

除非满足以下任一条件，否则不进入复杂自研 Build：

1. 涉及 authoritative product state。
2. 涉及权限、审计、合规或持久化真状态。
3. 涉及采购领域 hard gate。
4. 同一能力已经在至少两个 instance 中稳定复用。
5. 已证明模型原生能力无法满足可验收结果。

### 4. xiaocai 必须 Build 的能力

xiaocai 必须自有以下能力，不得交给模型、UI 或 provider 成为真状态 owner：

1. procurement domain semantics。
2. confirmed fields / missing fields / readiness。
3. allowed actions / blocked actions / blocked reasons。
4. requirement intake 的产品闭环。
5. workbench projection contract。
6. sourcing policy、route plan、evidence/candidate contract。
7. template / analysis / artifact 的采购语义。
8. project / member / permission 的业务策略。
9. tenant overlay 与 domain pack 的产品含义。

模型可以生成候选理解，但不能持有上述 authoritative truth。

### 5. FLARE / AgentRuntime 应 Build 的能力

FLARE / AgentRuntime 应逐步沉淀以下通用能力：

1. session / stream / patch / event runtime。
2. model provider router / fallback。
3. generic tracker / memory primitive。
4. generic tool / connector execution primitive。
5. generic retrieval routing carrier。
6. generic eval / trace / audit primitive。
7. industry pack execution hook。
8. canonical projection primitives。

这些能力不得包含 procurement-specific vocabulary，也不得反向吸收 xiaocai 的业务策略。

### 6. xiaocai 当前允许 Buy / Glue 的能力

当前阶段允许 Buy 或 Glue：

1. LLM provider。
2. model fallback 执行能力。
3. OCR。
4. vector recall。
5. external search。
6. MCP Gateway。
7. external database / supplier data source。
8. auth / identity 基础设施。
9. object storage / observability / deployment infrastructure。

所有 Buy / Glue 能力进入 xiaocai 前必须经过 adapter / provider boundary，并 normalize 成 xiaocai contract。

### 7. 行业脚手架复用标准

未来其他行业 instance 应复用此分层：

```text
FLARE / AgentRuntime
  generic runtime + model/tool/source/tracker/eval primitives

Industry Scaffold
  domain pack schema + industry hard gates + projection contract

Instance App
  tenant config + workbench semantics + delivery-specific glue
```

行业脚手架不应复制 FLARE runtime，也不应把行业规则写进 FLARE。

## Non-Goals

本 ADR 不在当前阶段要求：

1. 立即重写现有 tracker / extractor / scorer。
2. 立即把所有 Glue 能力上提到 FLARE。
3. 立即完成通用 AgentRuntime capability marketplace。
4. 立即替换现有 xiaocai 主流程。
5. 立即选择唯一 LLM provider、vector DB 或 MCP 实现。

## Consequences

正向影响：

1. 避免在会被模型能力快速覆盖的方向过度工程化。
2. 保留 xiaocai 产品真状态与采购闭环的控制权。
3. 允许当前版本通过 Glue 快速达到可演示、可验收目的。
4. 为 FLARE / AgentRuntime 后续沉淀通用能力提供衡量标准。
5. 为其他行业 instance 提供可复用的脚手架判断模板。

代价：

1. 当前会存在 Glue-first 的临时能力边界。
2. 需要持续维护能力归属表，避免 Glue 演变成隐式业务主逻辑。
3. 后续需要按成熟度分批把通用能力 Build 回 FLARE / AgentRuntime。

## Migration Rule

后续调整现有能力时，按以下顺序推进：

1. 先标注能力归属：Build / Buy / Glue / Model-native。
2. 再确认 authoritative state owner。
3. 若是 Model-native，优先收敛为 adapter + schema + eval。
4. 若是 xiaocai Build，保留在 xiaocai domain/application/workflow。
5. 若是 FLARE Build，必须去采购词汇后再进入 FLARE。
6. 若只是 Glue，不得进入 route、UI fallback 或 provider payload 直连 domain truth。

任何阶段都不得：

1. 让 UI 成为 authoritative product state owner。
2. 让 raw provider output 直接成为 domain truth。
3. 让 prompt 隐式承接长期业务规则。
4. 把 procurement-specific policy 下沉到 FLARE。
5. 因当前 Glue 方案存在，就默认永久放弃自有能力边界。

## Related

- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-004-instance-api-execution-baseline.md`
- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-006-instance-owned-sourcing-connectors-and-switchable-search.md`
- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-007-domain-prior-resolver-and-soft-bias-execution.md`
- `/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/10-xiaocai-instance-freeze-and-hard-refactor-plan.md`
- `/Users/dantevonalcatraz/Development/procurement-agents/docs/planning/README.md`
