# 第0章 xiaocai × FLARE 能力清单

> 版本 v0.1  
> 更新时间 2026-05-09

## 0.1 目的

本章用于说明 xiaocai 产品结合 FLARE / AgentRuntime 后，当前已经具备哪些能力、哪些能力只是部分具备、哪些能力还没有完成。

状态说明：

| 状态 | 含义 |
|---|---|
| Done | 已有代码、合同或测试支撑，可作为当前能力对外说明 |
| Partial | 已有入口或雏形，但还不是完整产品级闭环 |
| Planned | 已在 ADR / planning 中冻结方向，但尚未完成实现 |
| Not Yet | 当前仅作为未来能力，不应对外承诺已可用 |

## 0.2 总体分层

| 层 | 负责能力 | 当前状态 |
|---|---|---|
| FLARE / AgentRuntime | kernel runtime、stream、session primitive、model provider router、通用 tool/source/tracker/eval primitive | Partial |
| xiaocai instance | 采购语义、需求闭环、字段状态、工作台投影、寻源策略、权限策略、租户配置 | Partial |
| Glue / Adapter | LLM、外部搜索、MCP、外部数据库、OCR/vector/storage 的接入与 normalize | Partial |
| Manual / Eval | 使用手册、能力边界、smoke/eval case、验收口径 | Partial |

## 0.3 产品真状态能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| confirmed fields | xiaocai | Partial | canonical contract 已定义；session context 可持久化 `confirmed_fields`；chat prior 可根据 context 注入 filled fields | 还需把所有主流程统一切到 canonical state owner |
| missing fields | xiaocai | Partial | canonical contract 已定义；domain prior / pending contract 可输出 missing fields；测试覆盖 missing priority / relevance | 还需完成统一派生 owner，减少旧 fallback |
| readiness | xiaocai | Partial | canonical contract 已定义；domain prior 有 readiness score；pending contract 有 gate | 还需形成稳定 readiness contract 与 hard gate owner |
| current stage | xiaocai | Partial | canonical contract 已定义；domain prior 可输出 active stage | 还需统一 stage progression owner |
| allowed actions | xiaocai | Partial | canonical `next_actions` 已定义；pending contract 可输出 next actions | 还需和 workflow/action registry 收口 |
| blocked reasons | xiaocai | Partial | pending contract gate 可输出 reason，例如 low category confidence | 还需标准化 blocked reason enum / schema |
| workbench projection | xiaocai | Partial | pending contract / cards / metadata 可供前端展示 | 还需确认前端只消费投影，不反推真状态 |
| audit / persistence | xiaocai + FLARE | Partial | sessions、messages、context、sources、artifacts、project usage 已有持久化路径 | 还需统一审计事件、trace 与跨链路查询 |

## 0.4 采购领域能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| domain pack assets | xiaocai | Done | 字段总表、品类、术语、活动/礼品场景、推荐策略、静态校验 | 后续需补更多行业/租户覆盖样例 |
| domain pack context export | xiaocai | Partial | chat prior 能注入 analysis template、RFX template、domain prior | 需要正式 context export API / payload 手册化 |
| category prior | xiaocai | Partial | category candidate pool、confidence score、resolved path 已有测试 | 需减少硬编码 fallback，稳定 resolver contract |
| field prior | xiaocai | Partial | missing fields priority / relevance 已有测试 | 需统一字段 graph 与 canonical state 派生 |
| template recommendation | xiaocai | Partial | matched rules、candidate pool、score、fallback template 已有测试 | scorer 应保持轻量，模型解释走 Glue |
| hard gate | xiaocai | Partial | low confidence 时可阻断并追问 | 需形成明确 hard gate schema 和覆盖更多场景 |
| soft bias / scoring | xiaocai + Model Glue | Partial | 已有基础权重与候选排序 | 不应过度自研；需保留 eval 评估 |

## 0.5 模型原生能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| prompt / instruction | xiaocai + FLARE | Partial | domain prior / instruction hints 可进入 kernel context | 需要集中治理 prompt，避免散落 |
| field extraction | Model Glue + xiaocai contract | Partial | 现有 extractor / prior 可辅助识别 | 应收敛为模型候选 + normalize，不继续深挖硬编码 |
| dialogue tracking / track | FLARE Build later + xiaocai projection | Planned | session context 可保存 facts、unknowns、turns、evidence、analysis/sourcing results | 还没有通用 tracker primitive；当前应 Glue-first |
| question generation | Model Glue + xiaocai gate | Partial | pending question payload 已定义，低置信度可追问 | 需模型生成与 field policy 更稳定结合 |
| analysis generation | Model Glue + xiaocai artifact contract | Partial | chat/run 可调用 kernel；artifact 可存分析类 content | 需正式 analysis output schema 与导出闭环 |
| normalized output contract | xiaocai + FLARE | Partial | chat contract、canonical contract、integration contracts 已存在 | 需统一 provider/model 输出 normalize 入口 |
| fallback | FLARE | Partial | FLARE provider router 配置项已列入手册；xiaocai 不重写 provider router | 需完成联调与 fallback smoke |

## 0.6 寻源与证据能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| sourcing route plan | xiaocai | Partial | retrieval policy 可返回 route plan、ordered connector、attempt steps | 目前 attempt results 仍是 simulated |
| evidence contract | xiaocai | Partial | retrieval hits 有 source、file、snippet、score；context 可保存 evidence | 需正式 evidence schema 与 external result normalize |
| candidate contract | xiaocai | Partial | session context 支持 sourcing candidates / sourcing results | 需 supplier candidate schema、ranking、projection |
| connector registry | xiaocai | Done | connector registry、enabled、priority、type、status 合同已存在 | 需真实多 connector 执行 |
| search source policy | xiaocai | Done | default connector、fallback connectors、routing rules 合同已存在 | 需真实 routing execution |
| external search | Buy / Glue | Planned | healthcheck 与 connector 概念已有 | 还没有真实外部 search adapter |
| external database | Buy / Glue | Planned | xiaocai DB healthcheck 已有；mock DB 方案已在手册中定义 | 还没有外部只读 DB adapter |
| MCP Gateway | Buy / Glue now, FLARE Build later | Planned | connector 概念已有；MCP JSON-RPC 最小规范已写入手册 | 还没有 MCP JSON-RPC 最小交互实现 |

## 0.7 权限、可见性与协作能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| auth token | xiaocai / external auth | Done | mock auth、root auth、JWT encode/decode 已有测试 | 生产级外部身份源未接入 |
| project ownership | xiaocai | Done | project bind、mine/list、project access 校验已有测试 | 完整 project member 管理未完成 |
| permission / visibility | xiaocai | Partial | conversation/source/artifact private isolation 已有测试 | 字段级 visibility、能力级 access 还未完成 |
| project member roles | xiaocai | Planned | ADR 已冻结方向 | 角色更新、成员列表、细粒度权限未完成 |
| UI visibility projection | xiaocai | Planned | 原则已冻结：UI 只消费 backend projection | 需要后端输出 masked/readonly/disabled projection |

## 0.8 会话、资料与产物能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| sessions | xiaocai + FLARE | Done | create/list/get/delete/archive、mode persistence、message write 已有测试 | 需和 canonical workflow state 完全打通 |
| conversations | xiaocai | Done | project conversations 与 private isolation 已有测试 | project-shared 协作模型待完善 |
| sources | xiaocai | Done | upload/list/delete/search/folder/mark referenced/download isolation 已有测试 | OCR/解析/向量化未完成 |
| artifacts | xiaocai | Done | create/list/detail/export/delete、private isolation 已有代码与测试 | 需结构化 artifact builders 与正式导出格式 |
| usage limits | xiaocai | Done | daily user/project message usage 已有测试 | 更细能力级 quota 未完成 |

## 0.9 工程支撑能力

| 能力 | Owner | 状态 | 当前已有 | 主要缺口 |
|---|---|---|---|---|
| adapter boundary | xiaocai + FLARE | Partial | kernel client、integration contracts、retrieval router、storage stores 已有 | 外部 DB/MCP/search adapter 需补 |
| observability | FLARE + xiaocai | Partial | provider trace 作为验收目标；attempt results 可表达 routing 状态 | 还缺统一 trace viewer / audit query |
| eval case | xiaocai + FLARE | Partial | domain pack tests、API regression tests、security isolation tests 已有 | 还缺模型能力 eval set 与评分门禁 |
| smoke commands | xiaocai | Partial | domain pack 校验、API pytest 命令已写入 planning | 需补完整端到端联调脚本 |
| deployment config | xiaocai | Partial | `.env.example`、settings、storage migration 已有 | 生产 provider fallback 矩阵与外部 connector env 待冻结 |

## 0.10 当前可对外说明的能力

当前可以谨慎对外说明：

1. xiaocai 是运行在 FLARE 之上的采购 instance。
2. 已有采购 domain pack、字段、品类、术语、模板 prior。
3. 已有需求梳理所需的字段缺失、追问、gate、next action 的最小合同。
4. 已有 session、message、source、artifact、project ownership 的基础持久化。
5. 已有 connector registry、search source policy、retrieval route plan 的配置与模拟验收。
6. 已有 private visibility isolation 的基础安全测试。
7. LLM provider fallback 由 FLARE 负责，xiaocai 消费配置与 trace。

不应对外承诺为已完成：

1. 完整通用 tracker。
2. 完整 MCP JSON-RPC 接入。
3. 真实多源外部搜索执行。
4. 外部只读 DB adapter。
5. supplier candidate 正式 ranking contract。
6. 字段级权限矩阵。
7. 完整可视化 observability / audit console。
8. 生产级 OCR / vector recall。

## 0.11 下一步最小补齐顺序

1. 冻结 capability schema：把本章能力状态纳入周计划验收。
2. 完成 domain context export payload。
3. 完成 external DB / MCP / search 的最小 adapter 与 normalize。
4. 固化 evidence / supplier candidate contract。
5. 补 model-native eval cases：field extraction、track、question generation、analysis draft。
6. 补 provider fallback smoke。
7. 补 permission projection：hidden / masked / readonly / disabled。
