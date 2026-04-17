# FLARE Dependency Gap Log

更新时间: 2026-04-16
维护原则: 每完成一个 xiaocai P0 主线任务（TASK-DP-*），必须更新本日志。

## 记录字段说明
- gap_id
- 标题
- 所属阶段（fields / question_flow / sourcing / scorecard / rfx / artifacts / loader / runtime）
- 当前任务
- 现状
- xiaocai 是否可自行解决（yes / partial / no）
- 若不可完全解决，原因是什么
- 期望 FLARE 提供的能力
- 建议接口位置（loader / contract / runtime / canonical projection / validation / execution hook）
- 是否阻塞当前 P0
- 临时绕行方案
- 风险说明
- 建议优先级（P0 / P1 / P2）

---

## Gap Entries

| gap_id | 标题 | 所属阶段 | 当前任务 | 现状 | xiaocai 是否可自行解决 | 若不可完全解决，原因是什么 | 期望 FLARE 提供的能力 | 建议接口位置 | 是否阻塞当前 P0 | 临时绕行方案 | 风险说明 | 建议优先级 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GAP-001 | 通用 domain pack loader 能力缺失（多包标准挂载） | loader | TASK-DP-008 | 当前 adapter 主要按旧 `domain-pack` 结构读取，缺少统一多实例 pack mount 规范 | partial | instance 可做局部双读，但无法形成跨实例复用标准 | 提供标准 pack loader + mount 协议（版本、优先级、回退） | loader | 否 | 在 adapter 内临时实现新旧路径双读（temporary） | 继续扩展会导致各 instance loader 分叉 | P0 |
| GAP-002 | 规则执行 hook 未标准化 | question_flow / sourcing / rfx | TASK-DP-002/003/004/008 | 可先在 instance 本地解释规则，但缺统一执行入口 | partial | instance 可跑本地规则，但无法保证与其他实例一致执行语义 | 提供标准 rule execution hook（输入/输出/错误语义） | execution hook / runtime | 否 | instance 先本地执行并记录映射（temporary） | 后续迁移成本高，规则语义可能漂移 | P1 |
| GAP-003 | artifacts 建议输出缺少稳定 canonical projection | artifacts | TASK-DP-004/008 | 文档已定义 artifact specs，但通用 contract 投影仍不稳定 | partial | instance 可本地产出，但跨流程/跨实例的标准字段未统一 | 提供 artifacts/recommendations/evidence/process meta 的稳定投影 contract | canonical projection / contract | 否（当前可先本地产出） | 先在 instance 保持本地 artifact mapping（temporary） | 后续接 FLARE canonical 时存在字段回填与兼容风险 | P0 |
| GAP-004 | 通用 schema/validation 框架不足 | fields / scorecard / rfx | TASK-DP-006/007 | 可先用 instance 校验脚本，缺平台级统一校验框架 | partial | instance 校验可用但不可复用，不是平台能力 | 提供通用 schema + validation 插件式框架 | validation | 否 | 使用 `scripts/validate_domain_packs.py` 先兜底（temporary） | 多实例后会出现重复脚本与规则不一致 | P1 |
| GAP-005 | domain pack 与 canonical contract 的版本协商机制缺失 | runtime | TASK-DP-008 | 现有读取逻辑未显式声明 pack schema 版本兼容矩阵 | no | instance 无法定义平台级版本协商规则 | 提供 pack schema version negotiation 与 compatibility policy | contract / runtime | 否（短期） | 在 instance 文档中固定版本并手工控制（temporary） | 版本升级时可能造成静默不兼容 | P1 |
| GAP-006 | 跨实例可复用的推荐解释结构未统一 | sourcing / scorecard | TASK-DP-002/003/004 | 可定义本实例推荐解释字段，但缺平台统一推荐解释标准 | partial | instance 可定义字段，无法成为通用规范 | 提供 recommendation explanation 通用 contract（reasons/evidence/risk） | canonical projection / contract | 否 | 先按本实例字段输出并留映射层（temporary） | 后续横向复用与比较困难 | P2 |

---

## 每任务更新模板（执行时追加）

### TASK-DP-XXX 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
2. 本任务暴露了哪些 FLARE 缺口：
3. 哪些缺口阻塞当前进度：
4. 哪些缺口可以临时绕过：
5. 是否需要向 FLARE 发起单独任务：

### TASK-DP-001 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - 新增 `domain-packs/` P0 目录骨架：`shared/`、`activity_procurement/`、`gift_customization/`。
   - 新增最小说明文件：`domain-packs/README.md`、`domain-packs/shared/README.md`、`domain-packs/activity_procurement/README.md`、`domain-packs/gift_customization/README.md`。
2. 本任务暴露了哪些 FLARE 缺口：
   - 未新增新的 blocker 型缺口；已验证 `GAP-001`（标准 mount 机制）与本任务相关。
3. 哪些缺口阻塞当前进度：
   - 当前无阻塞。DP-002/003/004 可继续在 instance 层推进。
4. 哪些缺口可以临时绕过：
   - `GAP-001` 可通过 adapter 双读路径 temporary 绕过。
5. 是否需要向 FLARE 发起单独任务：
   - 是。已在 `docs/flare-handoff-tasks.md` 记录 `FLARE-TASK-001`。

### TASK-DP-002 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - `domain-packs/activity_procurement/fields.yaml`
   - `domain-packs/activity_procurement/question_flow.yaml`
   - `domain-packs/activity_procurement/analysis_template.md`
   - `domain-packs/activity_procurement/sourcing_rules.yaml`
   - `domain-packs/activity_procurement/supplier_scorecard.yaml`
   - `domain-packs/activity_procurement/artifact_mapping.yaml`
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-002`：规则执行 hook 未标准化（question_flow / sourcing / rfx 规则需统一执行入口）。
   - `GAP-006`：推荐解释结构未统一（scorecard 与 shortlist 解释字段尚无平台通用 contract）。
   - `GAP-003`（相关）：artifact 输出映射虽可本地定义，但 canonical projection 仍待稳定。
3. 哪些缺口阻塞当前进度：
   - 当前无 blocker。可继续 DP-003（gift pack）与 DP-004（shared）。
4. 哪些缺口可以临时绕过：
   - `GAP-002`：instance 本地规则执行（temporary）。
   - `GAP-006`：instance 本地 recommendation explanation 字段（temporary）。
   - `GAP-003`：先按本地 artifact mapping 输出（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 需要。已覆盖在 `docs/flare-handoff-tasks.md`：
     - `FLARE-TASK-002`（Rule Execution Hook）
     - `FLARE-TASK-003`（Canonical Projection）

### TASK-DP-003 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - `domain-packs/gift_customization/fields.yaml`
   - `domain-packs/gift_customization/question_flow.yaml`
   - `domain-packs/gift_customization/analysis_template.md`
   - `domain-packs/gift_customization/sourcing_rules.yaml`
   - `domain-packs/gift_customization/supplier_scorecard.yaml`
   - `domain-packs/gift_customization/artifact_mapping.yaml`
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-002`：规则执行 hook 未标准化（礼品场景补问、阻断、升级规则后续需统一执行入口）。
   - `GAP-006`：推荐解释结构未统一（礼品评分解释字段尚无平台通用 contract）。
   - `GAP-003`（相关）：artifact 映射输出与 canonical projection 的稳定映射仍待平台能力。
3. 哪些缺口阻塞当前进度：
   - 当前无 blocker。可继续 DP-004（shared 抽取）。
4. 哪些缺口可以临时绕过：
   - `GAP-002`：instance 本地规则执行（temporary）。
   - `GAP-006`：instance 本地推荐解释字段（temporary）。
   - `GAP-003`：instance 本地 artifact mapping 输出（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 需要。沿用并持续更新：
     - `FLARE-TASK-002`（Rule Execution Hook）
     - `FLARE-TASK-003`（Canonical Projection）

### TASK-DP-004 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - `domain-packs/shared/fields/common_fields.yaml`
   - `domain-packs/shared/rules/common_blocking_rules.yaml`
   - `domain-packs/shared/rules/rfx_rules.yaml`
   - `domain-packs/shared/artifacts/artifact_specs.yaml`
   - `domain-packs/shared/suppliers/common_supplier_gate.yaml`
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-003`：artifact specs 已定义，但 canonical projection 仍缺稳定平台契约。
   - `GAP-004`：shared 规则可在 instance 脚本校验，平台级 schema/validation 框架仍缺。
   - `GAP-002`：shared rules 需要通用 execution hook 才能跨实例复用。
3. 哪些缺口阻塞当前进度：
   - 当前无 blocker。可继续 DP-005（examples）与 DP-006（validate）。
4. 哪些缺口可以临时绕过：
   - `GAP-003`：instance 本地 artifact mapping + 输出（temporary）。
   - `GAP-004`：instance 脚本校验（temporary）。
   - `GAP-002`：instance 本地规则执行（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 需要。沿用并持续更新：
     - `FLARE-TASK-002`（Rule Execution Hook）
     - `FLARE-TASK-003`（Canonical Projection）
     - `FLARE-TASK-004`（Schema/Validation Framework）

### TASK-DP-005 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - 活动场景样例：`happy_path.yaml`、`missing_budget.yaml`、`urgent_event.yaml`
   - 礼品场景样例：`shallow_customization.yaml`、`deep_customization_vip.yaml`、`tight_deadline.yaml`
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-004`（相关）：样例可在 instance 本地用于校验，但平台缺统一 schema/fixture validation 框架。
3. 哪些缺口阻塞当前进度：
   - 当前无 blocker。可继续 DP-006（validate 脚本）。
4. 哪些缺口可以临时绕过：
   - `GAP-004`：先使用 instance 本地 validate + tests（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 是。沿用 `FLARE-TASK-004`（Schema/Validation Framework）。

### TASK-DP-006 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - 新增 `scripts/validate_domain_packs.py`。
   - 已覆盖：YAML可解析、必填键、字段去重、question_flow字段引用、artifact映射引用、scorecard维度完整、RFX四动作覆盖。
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-004`：当前校验为 instance 本地脚本，平台通用 schema/validation 框架仍缺。
3. 哪些缺口阻塞当前进度：
   - 当前无 blocker。可继续 DP-007（最小测试）。
4. 哪些缺口可以临时绕过：
   - `GAP-004`：继续使用 instance 本地校验脚本（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 是。沿用 `FLARE-TASK-004`（Schema/Validation Framework）。

### TASK-DP-007 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - `tests/domain_packs/test_activity_pack.py`
   - `tests/domain_packs/test_gift_pack.py`
   - `tests/domain_packs/test_rfx_rules.py`
   - `tests/domain_packs/test_supplier_scorecard.py`
   - 本地执行通过：`python3 -m unittest discover -s tests/domain_packs -p test_*.py -v`。
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-004`：测试目前基于 instance 本地校验与本地规则解释，缺平台统一 validation/test harness。
   - `GAP-002`（相关）：规则执行语义仍在 instance 本地模拟，平台 hook 未落地。
3. 哪些缺口阻塞当前进度：
   - 当前无 blocker。可继续 DP-008（最小 loader/mount 接入）。
4. 哪些缺口可以临时绕过：
   - `GAP-004`：使用 instance 本地 unittest + validate 脚本（temporary）。
   - `GAP-002`：在测试中使用本地规则匹配逻辑（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 是。沿用：
     - `FLARE-TASK-002`（Rule Execution Hook）
     - `FLARE-TASK-004`（Schema/Validation Framework）

### TASK-DP-008 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - 更新 `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/contract_loader.py`：
     - 新增 `PackMountSnapshot`
     - 新增 `load_pack_mount_snapshot()`
     - 新增 `new domain-packs` 探测逻辑
     - 保留 legacy `domain-pack` contract 读取路径，形成最小双读兼容
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-001`：当前仅是 instance 侧最小双读探测，仍缺平台级标准 loader/mount 机制。
   - `GAP-005`：pack schema 版本协商仍无平台能力。
   - `GAP-003`（相关）：新 pack 产物到 canonical projection 的统一投影未平台化。
3. 哪些缺口阻塞当前进度：
   - 当前不阻塞 xiaocai P0 资产化收口；但会阻塞跨实例标准化复用推进。
4. 哪些缺口可以临时绕过：
   - `GAP-001`：继续使用 instance adapter 双读（temporary）。
   - `GAP-005`：在 instance 侧固定版本+人工兼容检查（temporary）。
   - `GAP-003`：维持本地 artifact mapping 输出（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 是。沿用并继续跟踪：
     - `FLARE-TASK-001`（标准 Loader/Mount）
     - `FLARE-TASK-003`（Canonical Projection）
     - `FLARE-TASK-005`（Schema Version Compatibility）

### TASK-DP-011（计划项）预置缺口识别

| gap_id | 标题 | 所属阶段 | 当前任务 | 现状 | xiaocai 是否可自行解决 | 若不可完全解决，原因是什么 | 期望 FLARE 提供的能力 | 建议接口位置 | 是否阻塞当前 P0 | 临时绕行方案 | 风险说明 | 建议优先级 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GAP-007 | 推荐策略执行与解释投影未平台标准化 | artifacts / runtime | TASK-DP-011 | xiaocai 可定义推荐规则与权重，但跨实例统一执行与解释投影缺标准 | partial | instance 可本地算推荐，但缺统一执行/trace/投影 contract | recommendation execution hook + explanation canonical projection | execution hook / canonical projection | 否 | instance 本地规则执行并输出 explanation 字段（temporary） | 后续跨实例推荐结果不可比、可解释性口径不一致 | P1 |

### TASK-DP-011 更新记录
1. 本任务新增了哪些 xiaocai 本地资产：
   - `domain-packs/shared/rules/template_recommendation_rules.yaml`
   - `domain-packs/shared/rules/recommendation_policy_registry.yaml`
   - `domain-packs/shared/artifacts/recommendation_audit_schema.yaml`
   - `scripts/validate_domain_packs.py` 已补充推荐策略资产最小校验。
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-007`：推荐策略可在 instance 定义，但跨实例统一执行/解释投影仍缺平台标准能力。
3. 哪些缺口阻塞当前进度：
   - 当前不阻塞 xiaocai P0 版本收口；但会影响后续跨实例复用一致性。
4. 哪些缺口可以临时绕过：
   - `GAP-007`：instance 本地执行推荐策略并输出 explanation 字段（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 是。已在 `docs/flare-handoff-tasks.md` 记录 `FLARE-TASK-006`。

### DEV-UPLOAD-001 更新记录（附件存储与Context优先级）
1. 本任务新增了哪些 xiaocai 本地资产：
   - `project_sources` 记录新增元数据字段：`source_type/date_bucket/time_bucket/context_priority`。
   - 上传接口支持传入 `source_type/context_priority`，列表/上传响应返回新增字段。
   - 列表默认按 `context_priority ASC, created_at DESC` 排序。
2. 本任务暴露了哪些 FLARE 缺口：
   - xiaocai 已提供优先级信号，但 context 拼装与检索排序执行仍依赖 FLARE。
3. 哪些缺口阻塞当前进度：
   - 不阻塞本地存储与信号落盘；阻塞“统一检索执行效果一致性”。
4. 哪些缺口可以临时绕过：
   - 通过 xiaocai 侧 `context_priority` + `source_type` 输出给上游（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 建议复用 `FLARE-TASK-006`（推荐/解释执行能力）并新增检索优先级执行子项。

### DEV-RETRIEVAL-002 更新记录（检索策略输入结构）
1. 本任务新增了哪些 xiaocai 本地资产：
   - 新增 `storage/source_policy.py`，生成 `preferred_sources/source_weights/context_refs`。
   - `POST /retrieval/search` 响应新增 `retrieval_policy`。
   - 新增 `GET /retrieval/policy`，可直接获取项目检索策略信号。
2. 本任务暴露了哪些 FLARE 缺口：
   - xiaocai 输出的是策略信号，真正的多源召回排序与context拼装仍依赖FLARE标准执行。
3. 哪些缺口阻塞当前进度：
   - 不阻塞本地策略输出；阻塞跨实例统一执行一致性。
4. 哪些缺口可以临时绕过：
   - xiaocai 输出策略信号给上游消费（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 建议在 `FLARE-TASK-006` 下补“retrieval policy signal execution”子项。

### DEV-BRANDING-003 更新记录（品牌/主题/实例个性化配置）
1. 本任务新增了哪些 xiaocai 本地资产：
   - 新增 `storage/tenant_profile_store.py`，提供租户品牌配置持久化（product_name/logo/theme/feature_flags）。
   - 新增 `tenant_profile/router.py`，提供 `GET/PUT /tenant-profile` 最小接口。
   - `app.py` 挂载 tenant-profile 路由。
2. 本任务暴露了哪些 FLARE 缺口：
   - 无新增 blocker；该能力应在 instance 侧维护。
3. 哪些缺口阻塞当前进度：
   - 当前无阻塞。
4. 哪些缺口可以临时绕过：
   - 无需绕行。
5. 是否需要向 FLARE 发起单独任务：
   - 暂不需要（属于 xiaocai instance 自身品牌配置域）。

### DEV-CHAT-004 更新记录（chat上下文注入检索策略信号）
1. 本任务新增了哪些 xiaocai 本地资产：
   - 新增 `chat/context_policy.py`，在有 project_id 时注入 `retrieval_policy/context_refs`。
   - 在 `chat/router.py` 的 `/chat/run` 与 `/chat/stream` 调用该策略注入逻辑。
2. 本任务暴露了哪些 FLARE 缺口：
   - FLARE 仍需提供统一的 retrieval policy signal 执行与上下文编排标准能力。
3. 哪些缺口阻塞当前进度：
   - 不阻塞 instance 侧信号注入。
4. 哪些缺口可以临时绕过：
   - 通过 adapter 层注入策略信号（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 建议挂在 `FLARE-TASK-006` 下作为执行子项持续跟踪。

### DEV-PRIORITY-005 更新记录（资料优先级管理接口）
1. 本任务新增了哪些 xiaocai 本地资产：
   - `SourceStore.update_source_priority(...)`（已落盘）
   - `POST /sources/{source_id}/priority` 接口，支持按项目更新 `context_priority`。
2. 本任务暴露了哪些 FLARE 缺口：
   - 仍缺平台统一的 context weighting 执行入口；xiaocai 目前只提供信号与排序输入。
3. 哪些缺口阻塞当前进度：
   - 不阻塞当前 P0（instance 侧可完成优先级管理与输出）。
4. 哪些缺口可以临时绕过：
   - 在 instance adapter 层持续输出 `context_priority` 并由上游消费（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 建议继续挂在 `FLARE-TASK-006`（检索/推荐执行标准化）下跟踪，无需新增 blocker 任务。

### DEV-RECOMMEND-006 更新记录（推荐策略管理接口）
1. 本任务新增了哪些 xiaocai 本地资产：
   - 新增 `storage/recommendation_policy_store.py`，支持租户级 recommendation overrides 持久化。
   - 新增 `GET/PUT /recommendation-policy` 接口，读取 shared 基线策略并写入 tenant overrides。
   - `app.py` 已挂载 recommendation-policy 路由。
2. 本任务暴露了哪些 FLARE 缺口：
   - `GAP-007` 仍成立：instance 可管理策略，但跨实例统一执行与解释投影仍缺平台标准能力。
3. 哪些缺口阻塞当前进度：
   - 不阻塞当前 P0（管理与配置已可落地）。
4. 哪些缺口可以临时绕过：
   - 由 instance 输出基线策略+租户覆盖并作为上游输入（temporary）。
5. 是否需要向 FLARE 发起单独任务：
   - 继续复用 `FLARE-TASK-006` 跟踪，无新增 blocker。
