# xiaocai Backlog（Reprioritized for Domain-Pack First）

更新时间: 2026-04-16

## 本次重排结论
- 当前 P0 主线统一为：**domain pack 资产化 + 校验测试 + 最小挂载**。
- 不进入 UI 先行、不进入平台泛化、不扩展 P0 无关场景、不触碰 FLARE Core 主流程。

---

## 冻结 / 延后任务（旧主线）

以下任务在本轮统一标记为 `Deferred/Frozen`（以 `docs/discussions/task_board.csv` 为准）：

1. UI 先行与工作台扩展类
   - 代表任务: TASK-006, TASK-007, TASK-007A, TASK-009, TASK-010, TASK-013, TASK-017~019, TASK-021, TASK-024~026, TASK-029~033, TASK-035
2. 平台与账户泛化类（非当前 P0 主线）
   - 代表任务: TASK-002~004, TASK-014~016, TASK-020, TASK-026~032, TASK-038, TASK-048~053
3. 过早管理页/运营类
   - 代表任务: TASK-054
4. 可能触及 FLARE Core 主流程或非必要耦合改造类
   - 代表任务: TASK-005, TASK-008, TASK-040, TASK-056（全部延后到 domain pack 资产闭合后再评估）
5. P0 无关场景扩展与泛化测试包
   - 代表任务: TASK-036~037, TASK-041~047（保留历史参考，当前不作为执行入口）

> 说明：历史 `Done` 项保留为历史事实，不纳入当前执行主线。

---

## 新的 P0 主线任务（执行顺序）

## Task DP-001：建立 P0 资产目录结构
- 目标：创建 shared + activity_procurement + gift_customization 的运行时资产目录骨架。
- 输入文件：
  - `docs/domain-assets-map.md`
  - `docs/domain-scope.md`
- 输出文件：
  - `domain-packs/shared/**`
  - `domain-packs/activity_procurement/**`
  - `domain-packs/gift_customization/**`
- 验收标准：目录与占位文件齐全，命名与文档一致，可被后续校验脚本扫描。
- 不做什么：不改 FLARE Core；不做 UI。

## Task DP-002：activity pack 配置化
- 目标：把活动采购文档转成机器可读配置（fields/question_flow/analysis/sourcing/scorecard/artifact_mapping）。
- 输入文件：
  - `docs/activity-procurement-pack.md`
  - `docs/supplier-evaluation-framework.md`
  - `docs/artifact-output-spec.md`
- 输出文件：
  - `domain-packs/activity_procurement/fields.yaml`
  - `domain-packs/activity_procurement/question_flow.yaml`
  - `domain-packs/activity_procurement/analysis_template.md`
  - `domain-packs/activity_procurement/sourcing_rules.yaml`
  - `domain-packs/activity_procurement/supplier_scorecard.yaml`
  - `domain-packs/activity_procurement/artifact_mapping.yaml`
- 验收标准：字段分层、补问顺序、七段式分析、筛选规则、评分规则、产物映射均可解析且字段引用闭合。
- 不做什么：不新增活动外场景规则。

## Task DP-003：gift pack 配置化
- 目标：把礼品定制文档转成机器可读配置（fields/question_flow/analysis/sourcing/scorecard/artifact_mapping）。
- 输入文件：
  - `docs/gift-customization-pack.md`
  - `docs/supplier-evaluation-framework.md`
  - `docs/artifact-output-spec.md`
- 输出文件：
  - `domain-packs/gift_customization/fields.yaml`
  - `domain-packs/gift_customization/question_flow.yaml`
  - `domain-packs/gift_customization/analysis_template.md`
  - `domain-packs/gift_customization/sourcing_rules.yaml`
  - `domain-packs/gift_customization/supplier_scorecard.yaml`
  - `domain-packs/gift_customization/artifact_mapping.yaml`
- 验收标准：浅/深定制分流、决策因子、寻源 red flags、评分与产物映射可解析且闭合。
- 不做什么：不扩展礼品以外场景。

## Task DP-004：shared 规则抽取
- 目标：抽取共用字段、阻断规则、RFX 路由、通用产物规格、通用供应商门槛。
- 输入文件：
  - `docs/domain-assets-map.md`
  - `docs/rfx-routing-spec.md`
  - `docs/artifact-output-spec.md`
  - `docs/supplier-evaluation-framework.md`
- 输出文件：
  - `domain-packs/shared/fields/common_fields.yaml`
  - `domain-packs/shared/rules/common_blocking_rules.yaml`
  - `domain-packs/shared/rules/rfx_rules.yaml`
  - `domain-packs/shared/artifacts/artifact_specs.yaml`
  - `domain-packs/shared/suppliers/common_supplier_gate.yaml`
- 验收标准：shared 规则被两个 pack 引用；RFX 四动作覆盖齐全；无重复字段漂移。
- 不做什么：不做通用平台规则引擎。

## Task DP-005：examples / fixtures
- 目标：补齐每场景 3 个最小样例（正常路径 / 缺字段路径 / 强约束路径）。
- 输入文件：
  - `docs/activity-procurement-pack.md`
  - `docs/gift-customization-pack.md`
- 输出文件：
  - `domain-packs/activity_procurement/examples/*.yaml`（3个）
  - `domain-packs/gift_customization/examples/*.yaml`（3个）
- 验收标准：样例可被校验脚本读取，能触发补问、阻断、RFX 建议与评分分支。
- 不做什么：不做 Prompt 演示稿。

## Task DP-006：validate 脚本
- 目标：建立 domain packs 最小静态校验器。
- 输入文件：
  - `domain-packs/**`
- 输出文件：
  - `scripts/validate_domain_packs.py`
- 验收标准：至少校验 YAML 可解析、必填键、字段不重复、question_flow 引用闭合、artifact 映射闭合、scorecard 维度完整、RFX 四动作覆盖。
- 不做什么：不做线上运行态质量评估。

## Task DP-007：最小测试
- 目标：建立 domain packs 可回归测试。
- 输入文件：
  - `scripts/validate_domain_packs.py`
  - `domain-packs/**`
- 输出文件：
  - `tests/domain_packs/test_activity_pack.py`
  - `tests/domain_packs/test_gift_pack.py`
  - `tests/domain_packs/test_rfx_rules.py`
  - `tests/domain_packs/test_supplier_scorecard.py`
- 验收标准：activity/gift 校验通过；缺字段阻断生效；RFX 输出为四类动作之一；scorecard 输出为推荐/谨慎/淘汰之一。
- 不做什么：不做 UI E2E。

## Task DP-008：最小 loader / mount 接入
- 目标：以最小改动接入新 `domain-packs`，保留旧 `domain-pack` 兼容双读。
- 输入文件：
  - `domain-packs/**`
  - `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/contract_loader.py`
- 输出文件：
  - `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/contract_loader.py`（最小挂载改动）
  - 必要的最小配置路径说明（如有）
- 验收标准：本地可从新路径读取核心资产；旧路径可回退；不修改 FLARE Core 主流程。
- 不做什么：不重构 orchestration 主引擎。

---

## 执行门禁
1. 未完成 DP-001~DP-004，不进入任何 UI 任务。
2. 未完成 DP-006~DP-007，不进入挂载接入与联调。
3. DP-008 只允许最小接入，不允许扩展到平台改造。

---

## 并行硬要求：FLARE 依赖缺口持续输出

1. 每完成一个 `TASK-DP-*`，必须在 `docs/flare-dependency-gap-log.md` 追加该任务更新记录：
   - 本任务新增了哪些 xiaocai 本地资产
   - 本任务暴露了哪些 FLARE 缺口
   - 哪些缺口阻塞当前进度
   - 哪些缺口可以临时绕过
   - 是否需要向 FLARE 发起单独任务
2. 所有临时绕行必须标注 `temporary`，禁止永久硬编码替代平台能力。
3. 当出现 `xiaocai是否可自行解决 = no` 或 `partial 且不可长期绕行` 的 gap，必须同步更新 `docs/flare-handoff-tasks.md`。
4. 本要求是 P0 执行门禁的一部分，与 DP-001~DP-008 并行执行。

## Task DP-011：推荐策略管理资产化（模板/建议/时机/权重）
- 目标：把“推荐内容 + 推荐时机 + 推荐权重”做成可管理资产，不做UI。
- 输入文件：
  - `docs/activity-procurement-pack.md`
  - `docs/gift-customization-pack.md`
  - `docs/rfx-routing-spec.md`
  - `docs/artifact-output-spec.md`
- 输出文件：
  - `domain-packs/shared/rules/template_recommendation_rules.yaml`
  - `domain-packs/shared/rules/recommendation_policy_registry.yaml`
  - `domain-packs/shared/artifacts/recommendation_audit_schema.yaml`
- 验收标准：
  1) 可配置推荐触发条件、推荐权重、禁用条件、fallback；
  2) 推荐结果可解释（命中规则/权重/未满足条件）；
  3) 支持版本化字段（version/effective_at/owner/change_reason）。
- 不做什么：
  - 不做管理页面；
  - 不改 FLARE Core 主流程；
  - 不扩展 P0 以外新场景。

## Task DEV-005：资料优先级更新接口（context_priority）
- 目标：支持已上传资料的 context_priority 后续可调。
- 输入文件：
  - `adapters/http_api/src/xiaocai_instance_api/storage/source_store.py`
  - `adapters/http_api/src/xiaocai_instance_api/sources/router.py`
- 输出文件：
  - `adapters/http_api/src/xiaocai_instance_api/sources/router.py`（新增 `POST /sources/{source_id}/priority`）
- 验收标准：可按项目更新 source context_priority，权限校验与不存在返回一致。
- 不做什么：不做 UI 调整；不改 FLARE Core 执行逻辑。

## Task DEV-006：推荐策略管理接口（模板/时机/权重，无UI）
- 目标：提供 recommendation policy 的最小管理入口（基线读取 + tenant 覆盖写入）。
- 输入文件：
  - `domain-packs/shared/rules/template_recommendation_rules.yaml`
  - `domain-packs/shared/rules/recommendation_policy_registry.yaml`
  - `domain-packs/shared/artifacts/recommendation_audit_schema.yaml`
- 输出文件：
  - `adapters/http_api/src/xiaocai_instance_api/storage/recommendation_policy_store.py`
  - `adapters/http_api/src/xiaocai_instance_api/recommendation_policy/router.py`
  - `adapters/http_api/src/xiaocai_instance_api/app.py`
- 验收标准：`GET/PUT /recommendation-policy` 可读写策略覆盖配置，保留基线策略信息。
- 不做什么：不做推荐执行引擎；不做管理页面；不改 FLARE Core 主流程。
