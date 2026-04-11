# xiaocai instance As-Is Audit

## Scope

- 审计日期: 2026-04-10
- 审计对象: `domain-pack/` + `adapters/http_api/src/xiaocai_instance_api/` + `frame/web/src/`
- 审计目标: 提取当前真实实现（As-Is），不把文档意图当已实现能力。

---

## 1) FLARE Frozen Baseline Acknowledgement (Read-Only)

### 1.1 已读取且作为当前基线依据

- `docs/README.md`
- `docs/architecture/01-architecture-overview.md`
- `docs/architecture/02-kernel-runtime-engines.md`
- `docs/architecture/05-xiaocai-current-to-target-mapping.md`
- `docs/architecture/07-flare-instance-boundary.md`
- `docs/domain-standards/01-domain-scope-and-boundaries.md`

### 1.2 用户指定但当前仓库不存在（需显式记录）

- `docs/reports/2026-04-10-flare-doc-first-functional-audit.md`
- `docs/contracts/flare-v1-sse-patch.md`
- `docs/contracts/requirement-intake-canonical-v1.md`
- `docs/architecture/04-capability-matrix-and-gap-audit.md`
- `docs/architecture/02-kernel-instance-interface.md`（当前存在的是 `02-kernel-runtime-engines.md`）
- `contracts/kernel-contract-v1.md`

状态标签:
- `TO_CONFIRM`: 上述缺失文件是否在其他仓库（例如 FLARE 主仓）维护。
- `OUT_OF_SCOPE`: 本仓不改写 FLARE contract，仅引用现有边界文档。

---

## 2) Instance-Specific Asset Inventory (with evidence)

### 2.1 Domain Pack（配置层）

- 工作流: `domain-pack/workflows/procurement-workflow-nodes.yaml`
- 字段总表: `domain-pack/schema/procurement-field-dictionary.yaml`
- 实体与阶段必填: `domain-pack/schema/procurement.yaml`
- 术语与意图触发词: `domain-pack/terminology/procurement.yaml`
- 搜索/寻源/替换契约: `domain-pack/contracts/procurement-search-sourcing-replace.yaml`
- 分析与 RFX 模板契约: `domain-pack/contracts/procurement-analysis-rfx-templates.yaml`
- FLARE 映射草案: `domain-pack/contracts/flare-contract-mapping.yaml`
- 类目目录占位: `domain-pack/category-fields/procurement-category-fields.yaml`
- UI 卡片模板: `domain-pack/cards/procurement-ui-cards.yaml`
- 场景 fixture: `domain-pack/contracts/scenarios/*.yaml`
- 一致性校验脚本: `domain-pack/scripts/validate_domain_pack.rb`

状态标签:
- `IMPLEMENTED`: 配置文件和校验脚本齐全。
- `PARTIAL`: 多项能力仅停留在配置契约，未证实被 runtime 消费。

### 2.2 API Adapter（实例适配层）

- 入口与路由注册: `adapters/http_api/src/xiaocai_instance_api/app.py`
- Chat 转发: `adapters/http_api/src/xiaocai_instance_api/chat/router.py`
- Kernel 请求组装: `adapters/http_api/src/xiaocai_instance_api/chat/kernel_client.py`
- 认证与权限: `auth/*`, `security/*`
- 会话/消息/项目/来源/产物存储: `storage/*`, `sessions/router.py`, `projects/router.py`, `sources/router.py`, `artifacts/router.py`

状态标签:
- `IMPLEMENTED`: 会话、权限、消息持久化、source 上传/检索、artifact CRUD。
- `CODE_ONLY`: 运行侧能力主要是“代理 + 存储”，非采购业务编排。

### 2.3 Web Frame（实例 UI 壳）

- 主页面装配: `frame/web/src/pages/ChatPage.tsx`
- Chat 运行时对接: `frame/web/src/services/api.ts`, `backendRuntime.ts`
- 样式与外壳: `frame/web/src/index.css`

状态标签:
- `IMPLEMENTED`: ChatWorkspace 集成可用。
- `PARTIAL`: 业务流程切换仍依赖后端事件，前端未见本地 gate/transition policy 实施。

---

## 3) As-Is Capability Findings

### 3.1 Orchestration policy 雏形是否存在

结论: `PARTIAL`（配置有雏形，运行时未闭环）

证据:
- `domain-pack/workflows/procurement-workflow-nodes.yaml` 定义了 `stage_order`、`completion_rule`、`transitions`。
- 但 API 侧 `chat/router.py` 仅做鉴权、限流、session 管理并转发到 kernel；未读取 workflow YAML 执行 gate/transition。

标签:
- `DOC_ONLY`: 规则存在于配置。
- `CODE_ONLY`: API 没有对应执行器。

### 3.2 Domain pack 雏形是否存在

结论: `IMPLEMENTED`（配置资产齐全）

证据:
- 字段、模板、术语、search/replace、scenarios、mapping 文件齐全。
- `domain-pack/scripts/validate_domain_pack.rb` 对字段引用一致性、阶段顺序、模板变量、replace 规则做静态校验。

### 3.3 Prompt / Field / Template / Transition / Mapping 分布

- Prompt/引导文案: `domain-pack/branding/instance-branding.json` 与 `frame/web/src/pages/ChatPage.tsx`（默认 prompts）。
- Field schema: `domain-pack/schema/procurement-field-dictionary.yaml` + `domain-pack/schema/procurement.yaml`。
- Template: `domain-pack/contracts/procurement-analysis-rfx-templates.yaml`。
- Transition: `domain-pack/workflows/procurement-workflow-nodes.yaml`。
- Query mapping / replace: `domain-pack/contracts/procurement-search-sourcing-replace.yaml`。
- FLARE 接口映射草案: `domain-pack/contracts/flare-contract-mapping.yaml`。

状态标签:
- `IMPLEMENTED`: 文档与配置层。
- `PARTIAL`: 运行态消费链路不完整。

### 3.4 硬编码 vs 配置化

配置化:
- 工作流、字段、模板、术语、寻源/替换规则均在 `domain-pack`。

硬编码:
- `frame/web/src/pages/ChatPage.tsx` 中 `DEFAULT_FUNCTION_TYPE='intelligent_sourcing'`、`DEFAULT_STARTER_PROMPTS`、`CANVAS_UI_LABELS` 仍有内置默认值。
- API `settings.py` 中 `enabled_modes` 默认固定列表。

未实现/未证明:
- API 没有把 `FLARE_DOMAIN_PACK_ROOT` 用于加载业务规则执行。
- `flare-contract-mapping.yaml` 全部 `pending_flare_validation`。

标签:
- `DRIFTED`: 前端默认文案与 domain-pack 可并存，可能产生配置漂移。
- `MISPLACED`: 若后续把业务 gate 继续写在前端/adapter，将偏离 domain-pack 主体边界。

---

## 4) Critical Gaps (As-Is)

1. Orchestration policy 运行缺口
- 描述: gate/transition/readiness 只在配置，未见 instance 运行层执行。
- 标签: `PARTIAL`, `RISK`

2. 客户目标流程 A/B 的 entry-intent 校准未见显式策略实现
- 描述: “企业场景校准/个人需求提醒/继续检索分流”未形成可执行 policy 文件或运行逻辑。
- 标签: `DOC_ONLY`, `RISK`

3. 字段命名与客户目标存在映射空缺
- 描述: 已有 `候选数量`、`交付时间`，但客户提到的 `供应商数量`、`交期时长`、`对标企业`、`员工规模`、`买家资金`、`企业性质`、`社保人数` 未见同名字段。
- 标签: `TO_CONFIRM`, `PARTIAL`

4. FLARE 映射仍 pending
- 描述: `domain-pack/contracts/flare-contract-mapping.yaml` 所有 mapping 状态是 `pending_flare_validation`。
- 标签: `PARTIAL`, `RISK`

---

## 5) As-Is Status Tag Summary

- `IMPLEMENTED`
  - domain-pack 配置资产与校验脚本
  - instance API 的鉴权/会话/消息/source/artifact 基础能力
  - 前端 ChatWorkspace 装配与 starter prompts 读取

- `PARTIAL`
  - orchestration policy 的运行闭环
  - FLARE mapping 验证状态
  - 客户目标流程字段覆盖完整性

- `DOC_ONLY`
  - 多数业务策略（gate/transition/readiness）主要在文档与 YAML

- `CODE_ONLY`
  - API 的薄代理与存储能力已代码化，但不等价于采购业务能力

- `DRIFTED`
  - 前端默认 prompts/ui labels 与 domain-pack 配置双源

- `MISPLACED`
  - 若继续把流程策略放在 adapter/web，将偏离 domain-pack 作为业务承载层

- `RISK`
  - 客户流程落地缺少运行态 policy 执行器

- `DEFERRED`
  - workflow placeholders（supplier-search/quotation/negotiation/contract/delivery）

- `OUT_OF_SCOPE`
  - FLARE kernel contract 改写、平台状态机重构

- `TO_CONFIRM`
  - 缺失的 FLARE 基线文件位置
  - 客户新增字段是否为同义词映射或新字段

---

## 6) Next

1. 基于本审计先冻结 xiaocai To-Be 流程规范（不写实现）。
2. 做 As-Is vs To-Be 对齐并确定归属到 orch policy/domain pack/data/UI。
3. 输出可执行 backlog，先推进最小闭环链路。

---

## As-Is / To-Be / Gap / Next

- As-Is: domain-pack 配置基础较全，adapter/web 为薄壳，业务编排执行证据不足。
- To-Be: 以 xiaocai orch policy + domain pack + mapping 形成可执行流程。
- Gap: entry 校准、gate/transition/readiness、客户新增字段映射仍未收口。
- Next: 先完成目标流程规范与对齐表，再按 backlog 执行 P0。
