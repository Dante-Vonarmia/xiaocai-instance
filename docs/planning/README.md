# xiaocai Planning

最后更新: 2026-05-18

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
| `DATA-*` | Build | 数据契约、字段别名、字段归属属于 xiaocai 产品真状态 |
| `CANON-*` | Build + Handoff | readiness、hard blocker、权重口径由 xiaocai contract 冻结；真实运行由 FLARE 消费 |
| `OUT-*` | Glue | 分析文本由模型生成，但输出 schema、章节、阻断规则归 xiaocai contract |
| `TEST-*` | Build | 采购 eval / regression case 由 xiaocai 维护 |
| `HANDOFF-*` | Glue | xiaocai 输出合同与验收包，FLARE 承接 runtime 执行 |

冻结 ADR：

- [ADR-008 Build / Buy / Glue And Model-native Boundary](../adr/ADR-008-build-buy-glue-and-model-native-boundary.md)

## 3. 当前重点排期

### 3.0 当前执行基线（测试先行）

当前进入“排期对齐 → 测试/验收先行 → 小步实施”的执行方式。  
任何实现任务开始前，必须先完成以下检查：

1. 任务必须出现在本文件中，且有任务ID、状态、Owner、验收。
2. 先定义 contract / fixture / 测试命令，再进入代码实现。
3. 能写自动化测试的任务，先补测试或 fixture，再实现；不能自动化的文档/规划任务，先补验收清单。
4. 每次实现只允许推进一个小任务，不把结构性重构混进功能实现。
5. 未通过验收命令或人工验收清单的任务，不标记为 `Done`。

本阶段优先顺序：

```text
planning/status alignment
→ canonical quality gates
→ data contract fixtures
→ domain-pack regression tests
→ FLARE handoff package
→ implementation only after acceptance is explicit
```

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
| 2026-05-18 | planning 状态与测试先行门禁对齐 | `docs/planning/README.md` | 后续任务均有先验收/先测试规则 |
| 2026-05-19 | 数据契约字段与别名闭合 | `/Users/dantevonalcatraz/Downloads/数据契约和测试/数据契约20260411.xlsx` | 字段、别名、阶段归属与 domain-pack contract 可追溯 |
| 2026-05-20 | canonical readiness / 权重 contract 固化 | `docs/contracts/xiaocai-canonical-quality-gates.md` | 字段权重、阻断阈值、草稿阈值、可分析阈值可验收；不新增 runtime |
| 2026-05-21 | 分析/寻源输出模板 contract 补齐 | `domain-packs/contracts/procurement-analysis-rfx-templates.yaml` | 输出覆盖数据契约要求章节，字段依赖与缺字段阻断明确 |
| 2026-05-20 - 2026-05-22 | 分析报告模板投影串联与用户可见清洗 | `docs/planning/analysis-report-template-projection-plan.md` | 右侧报告按模板格式输出；内部代码、工作流、debug 概念不进入用户可见内容 |
| 2026-05-22 | 契约与 domain-pack 回归验收 | `tests/domain_packs/` | 字段别名、权重、评分、输出结构回归通过 |
| 2026-05-25 | FLARE handoff 包整理 | `docs/contracts/xiaocai-canonical-quality-gates.md` | canonical context 示例、字段策略、模板、验收命令可交付 |

### 3.2 采购智能配置中心排期

| 日期 | 任务 | 关联文档 | 验收 |
|---|---|---|---|
| 2026-05-25 | 配置中心范围冻结 | `planning/ai-configuration-center-plan.md` | P0 / P1 / P2 范围明确；不以裸 prompt 编辑器作为第一阶段目标 |
| 2026-05-26 | 品类配置 contract 设计 | `planning/ai-configuration-center-plan.md` | 字段、追问、分析维度、寻源偏好可表达 |
| 2026-05-27 | 模板配置 contract 设计 | `planning/ai-configuration-center-plan.md` | 章节、变量、字段依赖、草稿/确认态可表达 |
| 2026-05-28 | AI 规则 contract 设计 | `planning/ai-configuration-center-plan.md` | 全局、品类、模板、任务级规则边界清楚 |
| 2026-05-29 | 资料库接入边界设计 | `planning/ai-configuration-center-plan.md` | 资料库只作为 evidence/context，不成为真状态 |
| 2026-06-01 | 设置页 MVP 线框与预览流 | `planning/ai-configuration-center-plan.md` | 可从配置进入一次追问/分析预览 |
| 2026-06-02 | 开发任务拆分 | `planning/ai-configuration-center-plan.md` | 前端、backend contract、workflow、测试边界明确 |

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

### P0：Chat projection / fallback owner 收敛

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| CHAT-001 | 移除本地 orchestration fallback 与 adapter 伪造 pending | Done | xiaocai | legacy fallback 无残留引用；adapter projection 不覆盖 FLARE 输出；`adapters/http_api/tests` 通过 |
| CHAT-002 | auto 自然对话保护与梳理投影泄漏回归修复（instance 轻量化） | Done | xiaocai | `mode=auto` 不继承历史 intake 粘性；非显式梳理意图不生成需求梳理投影；普通对话不被缺字段策略阻断；局部失败降级为可继续对话；先补回归测试再改实现。测试清单：`docs/planning/chat-002-test-checklist.md`。验收命令：`.venv/bin/python -m pytest adapters/http_api/tests/test_chat.py adapters/http_api/tests/test_chat_prior_context.py adapters/http_api/tests/test_chat_stream_projection.py adapters/http_api/tests/test_chat_workbench_projection.py adapters/http_api/tests/test_chat_mode_regression.py -q`；结果：`45 passed in 16.63s`。 |
| CHAT-004 | Intake canonical runtime hardcode cleanup | Done | xiaocai | 清理伪确认值与 runtime 业务选项硬编码；模型/规则输出先进入 candidate，经字段字典和品类目录 canonical 后再进入 confirmed；验收清单：`docs/planning/chat-003-intake-canonical-acceptance-checklist.md#d-intake-canonical-防回归chat-004-必补`；验收命令：`.venv/bin/python -m pytest adapters/http_api/tests -q && .venv/bin/python -m pytest tests/domain_packs -q`；结果：`117 passed` + `19 passed, 42 subtests passed`。 |
| CHAT-005 | 分析报告模板投影串联与用户可见清洗 | Done | xiaocai | 已串联设置中心 prompt 模板、domain-pack 分析模板、字段归一化与右侧 `analysis_payload`；报告按 RFQ/RFX 业务格式展示；用户可见内容已清洗内部代码/工作流/debug 概念。验收命令：`.venv/bin/python -m pytest adapters/http_api/tests/test_analysis_content_schema_rules.py adapters/http_api/tests/test_chat_downstream_projection.py -q`；结果：`16 passed in 0.79s`；截图证据：`/var/folders/9g/23dgm0mj1sbc2g4wndwk9cr80000gn/T/TemporaryItems/NSIRD_screencaptureui_bc66am/Screenshot 2026-05-19 at 21.45.45.png`。 |

### P0：数据契约与 canonical 质量门禁（FLARE 执行前置）

> 边界：本组任务只冻结 xiaocai domain contract、字段权重、品类完整性、分析模板和验收 fixture。  
> 不在 xiaocai 内新增 workflow engine、追问逻辑、stream/canvas/pending runtime；真实执行由 FLARE 更新后承接。

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| DATA-001 | 数据契约字段 source 与别名闭合 | Done | xiaocai | `数量和单位`、`影响范围`、供应商寻源字段别名有明确映射；source 指向当前契约文件 |
| DATA-002 | 品类字段完整性矩阵 | Done | xiaocai | 每个一级/二级品类的必问、推荐问、可选字段可追溯，供 FLARE 追问消费 |
| CANON-001 | canonical readiness / 权重算法确认 | Done | xiaocai | 字段权重、品类字段权重、阻断阈值、草稿阈值、可分析阈值形成稳定 contract |
| CANON-002 | LLM candidate -> canonical field normalization contract | Done | xiaocai | canonical state 明确 `candidate_fields` / `confirmed_fields` / `rejected_candidates` / `field_history` 分层；模型输出默认不可直接成为 confirmed；anti-hardcode 门禁写入 canonical quality gates |
| OUT-001 | 需求分析与寻源输出模板 contract 补齐 | Done | xiaocai | 需求分析覆盖 7 段，寻源分析覆盖数据契约要求章节，字段依赖明确 |
| TEST-001 | 真实采购 case 验收集 | Done | xiaocai | case 覆盖期望追问字段、readiness 分数区间、可进入分析条件、模板段落 |
| HANDOFF-001 | FLARE 对接包 | Done | xiaocai + FLARE | canonical context 示例、字段策略、模板、验收标准可交给 FLARE 执行 |

### P1：文档体系治理

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| DOC-001 | docs 体系入口冻结 | Done | xiaocai | `docs/README.md` 与 governance 文档已建立 |
| DOC-002 | planning 入口建立 | Done | xiaocai | `docs/planning/README.md` 成为排期入口 |
| DOC-003 | 根目录历史文档分批吸收 | Planned | xiaocai | 根目录不再承接新增专题文档 |
| DOC-004 | Build / Buy / Glue 决策归属冻结 | Done | xiaocai | ADR-008 已建立；具体执行已落入本文件任务组 |

### P1：采购智能配置中心

| 任务ID | 任务 | 状态 | Owner | 验收 |
|---|---|---|---|---|
| CFG-001 | 配置中心产品范围冻结 | Planned | xiaocai | P0 / P1 / P2 范围明确，prompt 编辑不作为唯一控制面 |
| CFG-002 | 品类配置 schema 草案 | Planned | xiaocai | 品类字段、必填字段、推荐追问、分析维度、寻源偏好可表达 |
| CFG-003 | 模板配置 schema 草案 | Planned | xiaocai | 模板章节、变量、字段依赖、草稿/确认态可表达 |
| CFG-004 | AI 规则作用域与优先级 | Planned | xiaocai | 全局、品类、模板、任务级规则边界清楚 |
| CFG-005 | 资料库接入边界 | Planned | xiaocai | 资料库作为 evidence/context 输入，不成为 authoritative state |
| CFG-006 | 设置页 MVP 预览流 | Planned | xiaocai | 可预览追问、缺失字段、分析结构与模板依赖 |

## 5. 排期维护规则

1. 当前执行任务必须出现在本文件或本目录下的周计划文件中。
2. 每个任务必须有任务ID、状态、Owner、验收。
3. 每个实现任务必须先有对应 fixture / 测试命令 / 人工验收清单。
4. 测试或验收缺失时，任务只能保持 `Planned` 或 `In Progress`，不得标记 `Done`。
5. 架构原因写入 `architecture/`，不要写进任务表。
6. 业务规则写入 `domain-standards/`，不要写进任务表。
7. 合同字段写入 `contracts/`，不要写进任务表。
8. 历史任务只追溯，不直接覆盖当前排期。

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
