# xiaocai As-Is vs To-Be Alignment

## Scope

- 目标: 客户目标项与当前实现逐项对齐。
- 口径: 仅依据当前仓库代码与配置证据。

---

| 客户目标项 | 当前状态 | 状态标签 | 证据 | 差距说明 | 归属 |
|---|---|---|---|---|---|
| 企业场景校准 + 个人需求提醒 | 未见显式执行策略 | PARTIAL / RISK | `domain-pack/terminology/procurement.yaml`（仅 triggers）；`chat/router.py` 无此策略 | 有术语，无可执行 entry policy | orch policy |
| 无明确意图时持续检索澄清 | 文档/术语层有概念，运行态未证实 | DOC_ONLY | `docs/domain-standards/03-domain-workflows-and-stage-rules.md`，`terminology/procurement.yaml` | 缺显式“澄清循环”执行条件 | orch policy |
| 明确意图分流到梳理/分析/寻源 | workflow 有阶段，API 不执行分流 | PARTIAL | `workflows/procurement-workflow-nodes.yaml`；`chat/router.py` | 缺运行时 transition 执行器 | orch policy |
| 进入梳理/寻源前确认 5 核心字段 | 字段存在，gate 执行未证实 | PARTIAL | `schema/procurement-field-dictionary.yaml`，`schema/procurement.yaml` | 规则存在但未见 runtime gate | orch policy + field taxonomy |
| 流程 A: 检索 -> 寻源 | 合同层有 sourcing_rules | PARTIAL | `contracts/procurement-search-sourcing-replace.yaml` | 缺“检索到寻源”的运行态 readiness 实施证据 | orch policy + data |
| 流程 B: 检索 -> 梳理 -> 分析 -> RFX | workflow 定义到 rfx-strategy | PARTIAL | `workflows/procurement-workflow-nodes.yaml` | 运行侧只转发 kernel，无本仓编排执行 | orch policy |
| 智能寻源附加字段（产品/服务、区域等） | 大部分存在；部分缺失/待映射 | PARTIAL / TO_CONFIRM | `schema/procurement-field-dictionary.yaml`（有 供应商区域/候选数量） | `供应商数量/交期时长/对标企业` 等口径未定 | field taxonomy |
| 增强字段（员工规模/买家资金/企业性质/社保人数） | 未见同名字段 | TO_CONFIRM | dictionary 未命中 | 需确认新增或映射 | field taxonomy |
| 供应商数量映射策略 | 可临时 alias 到 `候选数量` | PARTIAL / TO_CONFIRM | `schema/procurement-field-dictionary.yaml`（`候选数量`） | 客户未确认前只能临时映射 | field taxonomy + sourcing |
| 交期时长映射策略 | 可临时 derived from `交付时间` | PARTIAL / TO_CONFIRM | dictionary 含 `交付时间`、`响应时效` | 派生规则需客户确认 | field taxonomy + sourcing |
| 对标企业/员工规模/买家资金/企业性质/社保人数 | 需 optional/defer 策略 | TO_CONFIRM / DEFERRED | dictionary 未命中 | v1 不宜作为 gate 阻断项 | field taxonomy + deferred |
| 需求梳理输出模板字段 | 模板与字段多已存在 | IMPLEMENTED / PARTIAL | `contracts/procurement-analysis-rfx-templates.yaml` + dictionary | 部分客户字段命名差异待统一 | template/output |
| 需求分析补充（技术/质量/验收/条款） | 已入 workflow/template/dictionary | IMPLEMENTED | `workflows/...` + `contracts/procurement-analysis-rfx-templates.yaml` | 需验证运行时阻断是否生效 | orch policy + template |
| RFX 支撑 | 模板与 allowed_types 已定义 | IMPLEMENTED / PARTIAL | `contracts/procurement-analysis-rfx-templates.yaml` | 缺与客户最终规则的一致性确认 | template/output |
| search mapping/evidence/replace history | 契约完整 | IMPLEMENTED | `contracts/procurement-search-sourcing-replace.yaml` | 执行链路与落盘联动待验证 | data mapping |
| FLARE 接口映射 | 有映射草案，全部 pending | PARTIAL / RISK | `contracts/flare-contract-mapping.yaml` | 尚未完成跨仓 contract validation | data mapping |
| UI 入口与 starter prompts | 已实现，且支持 branding 文件读取 | IMPLEMENTED / DRIFTED | `frame/web/src/pages/ChatPage.tsx`, `domain-pack/branding/instance-branding.json` | 默认值与配置双源 | UI |
| 会话/权限/项目隔离 | 已实现 | IMPLEMENTED | `security/*`, `sessions/router.py`, `projects/router.py`, `conversation_store.py` | 非业务差距项 | OUT_OF_SCOPE（业务流程） |
| kernel contract 改造 | 本仓未做改造 | OUT_OF_SCOPE | 架构边界文档 + 当前代码 | 应保持不变 | OUT_OF_SCOPE |

---

## P0-0 Freeze Linkage

1. TO_CONFIRM 冻结矩阵:
- `docs/domain-standards/xiaocai-instance-alignment/xiaocai-to-confirm-freeze-matrix.md`
2. 字段映射收口:
- `docs/domain-standards/xiaocai-instance-alignment/xiaocai-field-mapping-closure-spec.md`

规则:

1. 若 BLOCKER 项未确认，则 `P0-1 orch policy pack v1` 不开工。
2. 若采用默认值推进，必须在 policy 文档中显式标注 temporary defaults。

## As-Is / To-Be / Gap / Next

- As-Is: 配置契约强，运行编排弱；基础壳能力完整。
- To-Be: 以 orch policy + field taxonomy + mapping validation 驱动流程 A/B。
- Gap: P0 在 TO_CONFIRM freeze 与字段口径收口，不在 UI 外观。
- Next: 先做 P0-0 + P0-2，再进入 P0-1。
