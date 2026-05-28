# xiaocai instance 边界与目录冻结（锁版）

> 当前肃清原则：xiaocai 是采购 instance，不是 FLARE kernel/runtime 的替代实现。  
> xiaocai 只承接使用层、配置层、业务资产层和必要 adapter；缺 runtime 能力时回到 FLARE，不在本仓库补一套底层机制。

## 1. 分层边界冻结

| 层 | 负责什么 | 不负责什么 |
|---|---|---|
| transport/router | auth/session/sse/contract 出口，调用 FLARE / adapter | 业务决策、字段选择、问题生成、workflow 推进 |
| instance API facade | 用户、项目、会话、资料、权限、source/MCP 配置与 kernel 调用 | 替代 FLARE kernel、mode runtime、stream runtime |
| domain pack / config | 采购字段、品类、模板、术语、场景规则、MCP/source 映射 | 主流程控制、mode 自动切换、canvas 真状态、readiness runtime |
| adapters/connectors | 调用外部 MCP、资料库、供应商库、搜索或 LLM provider，并 normalize 输出 | 采购业务真状态、workflow 阶段推进 |
| repositories | project/session/source/knowledge 持久化 | 业务编排、readiness、下一步动作 |
| projection mapping | 将 FLARE / xiaocai contract 映射给前端展示 | 发明 authoritative state、反向驱动后端 workflow |

历史文档中提到的 `canonical state`、`policy/field graph`、`workitem planner`、`executors`、`artifact builders` 等概念，如果属于通用运行机制，应优先归 FLARE；xiaocai 只保留采购 domain contract、adapter 使用层和必要的投影映射。

## 2. 目录冻结（后端）

```
adapters/http_api/src/xiaocai_instance_api/
  chat/
    orchestration/
      contract_loader.py      # 读取/映射 pack 与合同；不得扩展成 workflow engine
      prior_context.py        # 仅提供 domain prior；不得控制主流程
      flare_intake_contract.py # 兼容桥接；真实 intake runtime 归 FLARE
  repositories/
    project/
    knowledge/
  storage/
  retrieval/
  sources/

domain-packs/
  schema/
  category-fields/
  contracts/
  shared/
  activity_procurement/
  gift_customization/
```

不冻结为新增目标的目录：

```
domain/state/
domain/policy/
domain/workitems/
domain/executors/
domain/artifacts/
```

除非后续有明确的 instance 使用层需求，否则不得按这些目录补一套本地 runtime。

## 3. 目录冻结（文档）

```
docs/
  architecture/
    08-xiaocai-instance-technical-scope-and-route-freeze.md
    09-xiaocai-instance-boundary-and-directory-freeze.md
  contracts/
    xiaocai-instance-canonical-contract.md
```

## 4. 兼容层冻结

1. `chat/orchestration/flows.py` 仅作为过渡 fallback，不新增业务能力。
2. `router` 中 pending_contract 推断逻辑仅允许保留兼容映射，不允许继续扩展业务语义。
3. 前端兜底逻辑仅保留渲染容错，不得参与业务判断。

## 5. 当前肃清检查项

每次改动前先归类：

| 类型 | xiaocai 处理方式 |
|---|---|
| 采购字段 / 品类 / 模板 / 术语 / 供应商规则 | 留在 domain pack / contract |
| 用户 / 项目 / 会话 / 权限 / 上传 / source / MCP 配置 | 留在 instance API 使用层 |
| LLM/provider/MCP 调用 | 通过 adapter 调用并 normalize |
| mode / workflow / readiness / question planning / canvas canonical / stream / patch | 不在 xiaocai 开发，转 FLARE 缺口 |
| UI 展示 | 消费后端投影，不发明真状态 |

当前允许的短期兼容代码必须满足：

1. 只做输入输出映射或兼容桥接。
2. 不新增业务规则。
3. 不改变主 workflow。
4. 有明确删除或上收到 FLARE 的方向。

## 6. CLEAN-002 本地 runtime-like 逻辑审计

审计日期：2026-05-22

审计范围：

- `adapters/http_api/src/xiaocai_instance_api/chat/router.py`
- `adapters/http_api/src/xiaocai_instance_api/chat/workbench_projection.py`
- `adapters/http_api/src/xiaocai_instance_api/chat/context_policy.py`
- `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/*`
- 审计中发现被 router 直接依赖的相邻 projection / fallback helper 一并记录。

### 6.1 审计结论表

| 文件/模块 | 当前合理职责 | runtime-like 风险 | 处理结论 |
|---|---|---|---|
| `chat/router.py` | instance API facade：auth、session、limit、project scope、调用 FLARE kernel、SSE 转发、会话写回 | 文件过大；包含 `_build_pending_contract`、adapter-side `next_actions`、`canvas_state`、analysis/sourcing projection fallback、空回复 fallback，容易变成本地 runtime | 保留 transport/facade；冻结 pending/canvas/next_action/projection fallback 扩展；后续按 FLARE native contract 收敛或删除 |
| `chat/context_policy.py` | 组装 kernel context：auth scope、retrieval policy、domain prior、prompt/config 输入 | 注入 `clarification_policy`、`confidence_policy`、`domain_system_prompt`，可能影响模型行为和流程表现 | 保留为输入组装层；不得决定 workflow；prompt/domain injection 后续需对齐 FLARE context injection contract |
| `chat/workbench_projection.py` | 将 FLARE/native pending 或兼容 pending 映射为前端 canvas payload | 本地计算 required/missing/progress/ready_for_submit/current_question/next_actions，接近 canvas canonical runtime | 仅作为兼容投影保留；不得新增采购包/draft/workflow 能力；FLARE canvas_state 足够后删除或降级为 shape mapping |
| `chat/pending_policy.py` | 将 policy trace 附加到已有 pending contract | 当前不合成问题，风险较低 | 保留；只能附加 trace，不能生成 pending/question |
| `chat/display_projection.py` | FLARE 无可展示文本时的用户可见兜底 | 会生成初版寻源方案、待确认清单、intake markdown，容易替代 FLARE 正式输出 | 冻结；只允许短期兜底；后续由 FLARE output/projection 统一承接 |
| `chat/analysis_projection.py` / `chat/sourcing_projection.py` | 将采购模板/候选信息映射为右侧结构化展示 | 本地生成 analysis/sourcing 用户可见结构，可能变成本地 artifact runtime | 保留为 instance projection mapping；不得承担分析/寻源执行；若 FLARE 提供 native projection，应迁移 |
| `orchestration/contract_loader.py` | 读取 xiaocai domain-pack / contract 资产并转为输入数据 | 手写解析 pack、读取 workflow/stage required 字段；若继续扩展会变成本地 pack runtime | 保留读取/映射；不新增执行语义；后续对齐 FLARE 标准 domain-pack loader |
| `orchestration/prior_context.py` | 组装采购 domain prior、模板、品类/字段提示输入 | 本地计算 active_stage、missing_fields、readiness_score、clarification_policy、confidence_policy，已经接近本地 policy/runtime | 高风险；冻结扩展；后续拆分为纯 prior export，readiness/clarification/confidence 运行机制回 FLARE |
| `orchestration/flare_intake_contract.py` | 将 xiaocai procurement context 映射为 FLARE intake 输入 | 本地生成 required_missing、field_definitions、confirmed_fields、candidate_fields、field_history | 作为兼容桥保留；不得成为 authoritative intake runtime；后续对齐 FLARE domain-pack driven intake 接口 |
| `orchestration/mode_resolution.py` | 显式 request/session mode 的轻量解析 | 已移除 message keyword 推断；当前风险低 | 保留；继续禁止自然语言关键词自动切 mode |
| `orchestration/extractor.py` | 从文本中抽取预算、数量、时间、地点等候选字段 | `extract_slots` 可作为候选来源；未使用的 `detect_intent` 若接回主链会重新制造本地 intent runtime | 仅作为 candidate extraction 使用；不得驱动 mode/workflow；未使用 intent helper 后续可清理 |
| `orchestration/taxonomy_prior.py`、`template_prior.py`、`relevance_prior.py`、`field_prior.py`、`threshold_prior.py` | 从 domain pack 计算 category/template/field relevance prior | 计算分数、阈值、clarification action，容易从 prior 变成 runtime decision | 暂作为 advisory prior；不得直接控制 workflow/readiness；规则执行与阈值解释能力应回 FLARE |
| `orchestration/config_prompts.py` | 将设置中心 prompt/domain prompt 编译为模型输入 | prompt 可能把内部 stage/workflow 语义暴露给用户可见回复 | 保留但需审计用户可见污染；不允许用 prompt 替代 workflow/runtime |
| `orchestration/field_candidates.py` / `question_options.py` | normalize candidates/options | 职责清晰，风险较低 | 保留为 normalization helper |

### 6.2 本轮禁止继续扩展的本地能力

以下能力如果继续需要，必须转为 FLARE 缺口，不在 xiaocai 本地补：

1. pending contract 合成。
2. canvas canonical state 合成。
3. readiness / confidence / clarification runtime。
4. question planning / next_actions 生成。
5. mode / workflow 自动推进。
6. analysis / sourcing artifact runtime。
7. domain-pack loader / rule execution runtime。

### 6.3 保留的 xiaocai 使用层能力

以下能力继续留在 xiaocai：

1. auth、membership、project、session、source、upload、permission。
2. kernel 调用 facade 与 SSE 转发。
3. domain-pack / contract 资产维护。
4. 外部 DB、MCP、供应商库、资料库 adapter 与配置。
5. provider / MCP / LLM 输出 normalization。
6. 将 FLARE 输出映射为 xiaocai 前端可消费的展示 payload。

### 6.4 后续任务入口

- `CLEAN-003`：继续审计 `domain-packs/**`，把 knowledge/config/prompt-hint/projection-hint/runtime-control 分类。
- `CLEAN-004`：整理 xiaocai 当前精准能力表。
- `CLEAN-005`：把本节列出的 runtime 缺口回传 FLARE。
