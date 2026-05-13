# xiaocai Planning

最后更新: 2026-05-11

## 1. 目的

本目录是 xiaocai 当前任务排期的唯一正式入口。  
后续所有周计划、里程碑、验收门禁和当前执行状态都应先进入这里，再引用 architecture / contracts / manual。

## 2. 与历史任务表的关系

- `docs/discussions/task_board.csv`：历史任务账本，保留追溯，不再作为当前排期唯一入口。
- `docs/architecture/*.md`：说明为什么做、边界是什么，不承接日常任务看板。
- `docs/planning/README.md`：说明现在做什么、何时做、怎么验收。

## 2.1 FLARE 对接文档发现规则

不要依赖单个绝对路径作为唯一依据。查找 FLARE 对接文档与接口规范时，按以下顺序发现：

1. 先定位 FLARE 仓库根目录。
   - 优先使用当前工作区旁边的 FLARE repo。
   - 若路径不确定，搜索包含 `docs/README.md` 且仓库名/README 指向 `F.L.A.R.E` 或 `FLARE` 的目录。
   - 若仍无法唯一确定，必须向维护者确认，不猜路径。
2. 读取 FLARE `docs/README.md`。
   - 这是 FLARE 文档入口索引。
   - 先从这里确认 planning、contracts、architecture 的当前入口。
3. 查找 planning / handoff。
   - 优先找 `docs/planning/README.md`。
   - 再找 `docs/planning/*handoff*.md` 或包含 `xiaocai`、`handoff`、`planning` 的文档。
4. 查找接口协议与稳定合同。
   - Kernel / stream / agent：`docs/contracts/core/`
   - Instance / files / sources / sessions / errors：`docs/contracts/integration/`
   - Runtime / sourcing / thresholds：`docs/contracts/runtime/`
   - Analysis：`docs/contracts/analysis/`
5. 查找架构边界。
   - 优先看 FLARE `docs/architecture/README.md`。
   - 再看与 `instance`、`update-plane`、`provider`、`sourcing`、`authorization` 相关的 architecture 文档。

当前已知 FLARE 侧入口示例：

- `docs/planning/README.md`
- `docs/planning/xiaocai-handoff.md`
- `docs/contracts/README.md`
- `docs/architecture/README.md`

边界：

1. FLARE 负责合同、边界、交接、验收。
2. xiaocai 负责 instance 落地、domain pack、connector/mock DB/MCP、tenant/deploy 配置与联调执行。
3. 合同变更仍以 FLARE `docs/contracts/` 与 xiaocai `docs/contracts/` 为准。
4. 如果 planning 与 contracts 冲突，以 contracts 为准；如果 handoff 与 architecture 冲突，先按 architecture 边界复核。

## 2.2 Build / Buy / Glue 排期体现规则

Build / Buy / Glue 是架构决策，不单独维护任务型执行文件。  
决策依据写入 ADR；具体执行必须直接落到本文件的任务分组。

当前排期体现：

| 排期任务组 | Build / Buy / Glue 口径 | 说明 |
|---|---|---|
| `INT-*` | Buy / Glue | MCP、外部 DB、connector 接入不自研基础设施，xiaocai 负责 adapter、normalize、trace |
| `LLM-FB-*` | Buy / Reuse | LLM provider fallback 复用 FLARE 能力，xiaocai 只消费配置与 trace |
| `DATA-*` | Build | 数据契约、字段别名、readiness owner 属于 xiaocai 产品真状态 |
| `CALC-*` | Build + Glue | 权重计算由 xiaocai 承接；模型只参与解释与候选生成 |
| `SCORE-*` | Build | 供应商门槛、评分、推荐等级属于采购领域规则 |
| `OUT-*` | Glue | 分析文本由模型生成，但输出 schema、章节、阻断规则归 xiaocai contract |
| `TEST-*` | Build | 采购 eval / regression case 由 xiaocai 维护 |

冻结 ADR：

- [ADR-008 Build / Buy / Glue And Model-native Boundary](../adr/ADR-008-build-buy-glue-and-model-native-boundary.md)

## 3. 当前重点排期

| 日期 | 任务 | 关联文档 | 验收 |
|---|---|---|---|
| 2026-05-11 | 冻结接入合同与 fixture 设计 | `architecture/11-xiaocai-flare-db-mcp-integration-plan.md` | connector/provider 输入输出清楚 |
| 2026-05-12 | domain pack context export + provider 配置落点 | `manual-public/01-domain-pack-context.md` | domain context 可输出；env 示例明确 |
| 2026-05-13 | mock DB 接入 + provider health/quota 降级 | `manual-public/02-external-data-and-mcp-runbook.md` | DB sample query 通过；disabled/exhausted provider 自动跳过 |
| 2026-05-14 | mock MCP Gateway + provider timeout/fallback | `manual-public/02-external-data-and-mcp-runbook.md` | MCP JSON-RPC 可调用；fallback 有 trace |
| 2026-05-15 | 端到端通道验收 | `architecture/11-xiaocai-flare-db-mcp-integration-plan.md` | smoke tests 与手册步骤通过 |

### 3.1 接入后产品闭环排期

| 日期 | 任务 | 关联文档 | 验收 |
|---|---|---|---|
| 2026-05-18 | 数据契约字段与别名闭合 | `/Users/dantevonalcatraz/Downloads/数据契约和测试/数据契约20260411.xlsx` | 字段、别名、阶段归属与 domain-pack contract 可追溯 |
| 2026-05-19 | 权重计算 runtime 化 | `domain-packs/shared/rules/template_recommendation_rules.yaml` | 推荐结果包含命中规则、基础权重、修正因子、最终得分 |
| 2026-05-20 | 供应商 scorecard 计算闭环 | `domain-packs/*/supplier_scorecard.yaml` | supplier data 可计算门槛、维度得分、总分、推荐等级与解释 |
| 2026-05-21 | 分析/寻源输出模板补齐 | `domain-packs/contracts/procurement-analysis-rfx-templates.yaml` | 输出覆盖数据契约要求章节，缺字段阻断明确 |
| 2026-05-22 | 契约与权重回归验收 | `tests/domain_packs/` | 字段别名、权重、评分、输出结构回归通过 |

## 4. 当前任务分组

### P0：下周联调闭环

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| INT-001 | connector / mock DB / MCP fixture 合同冻结 | Planned | xiaocai | 输入输出、错误语义、trace 字段明确 |
| INT-002 | domain pack context export | Planned | xiaocai | taxonomy / terminology / field policy 可输出 |
| INT-003 | mock external DB 接入 | Planned | xiaocai | 至少 supplier 与 price/case 两类 mock 数据源 |
| INT-004 | mock MCP Gateway 接入 | Planned | xiaocai | `initialize`、`tools/list`、`tools/call` 可用 |
| INT-005 | retrieval route plan 联调 | Planned | xiaocai + FLARE | route plan / attempt results / evidence trace 可见 |

### P0：LLM Provider 降级链条

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| LLM-FB-001 | provider 降级输入合同冻结 | Planned | FLARE + xiaocai | candidates / health / quota / fallback / timeout 配置矩阵明确 |
| LLM-FB-002 | xiaocai env/deploy 消费配置 | Planned | xiaocai | 可通过 env 切换候选模型、健康状态、额度状态 |
| LLM-FB-003 | health/quota 降级回归 | Planned | FLARE + xiaocai | disabled/exhausted provider 被跳过 |
| LLM-FB-004 | timeout/error fallback 回归 | Planned | FLARE + xiaocai | primary timeout/500 返回 fallback 并记录 `provider_trace` |
| LLM-FB-005 | chat/retrieval 联合验收 | Planned | xiaocai | 回复不中断，降级原因可审计 |

### P0：数据契约与权重计算闭环

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| DATA-001 | 数据契约字段 source 与别名闭合 | Planned | xiaocai | `数量和单位`、`影响范围`、供应商寻源字段别名有明确映射；source 指向当前契约文件 |
| DATA-002 | contract loader / prior 使用统一字段口径 | Planned | xiaocai | 推荐规则、缺字段优先级、readiness 计算不再混用中英文字段 |
| CALC-001 | 模板推荐权重计算 runtime 化 | Planned | xiaocai | 输出命中规则、基础权重、readiness 修正、缺字段惩罚、最终排序 |
| CALC-002 | 场景过滤与禁用条件执行 | Planned | xiaocai | activity/gift 等规则不会跨场景误命中；禁用条件有可审计原因 |
| SCORE-001 | 供应商 scorecard calculator | Planned | xiaocai | 基于 hard gates、score dimensions、veto items 生成总分、等级、解释 |
| OUT-001 | 需求分析与寻源输出模板补齐 | Planned | xiaocai | 需求分析覆盖 7 段，寻源分析覆盖数据契约要求章节 |
| TEST-001 | 数据契约与权重计算回归测试 | Planned | xiaocai | domain-pack validation、alias、weight、scorecard、output snapshot 测试通过 |

### P1：文档体系治理

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| DOC-001 | docs 体系入口冻结 | Done | xiaocai | `docs/README.md` 与 governance 文档已建立 |
| DOC-002 | planning 入口建立 | Done | xiaocai | `docs/planning/README.md` 成为排期入口 |
| DOC-003 | 根目录历史文档分批吸收 | Planned | xiaocai | 根目录不再承接新增专题文档 |
| DOC-004 | Build / Buy / Glue 决策归属冻结 | Done | xiaocai | ADR-008 已建立；具体执行已落入本文件任务组 |

## 5. 排期维护规则

1. 当前执行任务必须出现在本文件或本目录下的周计划文件中。
2. 每个任务必须有任务ID、状态、Owner、验收。
3. 架构原因写入 `architecture/`，不要写进任务表。
4. 业务规则写入 `domain-standards/`，不要写进任务表。
5. 合同字段写入 `contracts/`，不要写进任务表。
6. 历史任务只追溯，不直接覆盖当前排期。

## 6. 状态枚举

- `Planned`
- `In Progress`
- `Blocked`
- `Done`
- `Deferred`

## 7. 不做什么

1. 不把 `docs/discussions/task_board.csv` 当作唯一当前看板。
2. 不在 architecture 文档里维护长期任务流水账。
3. 不把未验收的任务标记为 Done。
