# FLARE Handoff Tasks（from xiaocai P0）

更新时间: 2026-04-16
来源: `docs/flare-dependency-gap-log.md`

## FLARE-TASK-001
- task_id: FLARE-TASK-001
- 标题: 标准化 Domain Pack Loader / Mount 机制
- 背景: xiaocai 正在从文档资产化推进到多 pack（shared + 场景 pack）结构。
- 当前 xiaocai 遇到的问题: adapter 可临时双读新旧路径，但缺平台标准挂载协议。
- 需要 FLARE 提供什么: 统一 loader（路径/版本/优先级/回退）能力。
- 为什么不应在 instance 内解决: 该能力属于跨实例复用平台能力，instance 内实现会造成重复和漂移。
- 验收标准:
  1) 支持标准 pack mount 配置；
  2) 支持版本兼容与回退；
  3) 至少两个实例可复用同一 loader。
- 优先级: P0

## FLARE-TASK-002
- task_id: FLARE-TASK-002
- 标题: 规则执行通用 Hook（Rule Execution Hook）
- 背景: xiaocai 需要执行 question_flow/sourcing/rfx 规则。
- 当前 xiaocai 遇到的问题: 可在 instance 本地执行规则，但缺标准执行入口与错误语义。
- 需要 FLARE 提供什么: 通用规则执行 hook（输入/输出/错误/trace）。
- 为什么不应在 instance 内解决: 多实例场景下，规则执行语义应由平台统一，不应分散在各 instance。
- 验收标准:
  1) 可注册并执行规则；
  2) 返回结构统一；
  3) 有最小 trace 信息。
- 优先级: P1

## FLARE-TASK-003
- task_id: FLARE-TASK-003
- 标题: Canonical Projection 扩展（Artifacts / Recommendations / Evidence / Process Meta）
- 背景: xiaocai 已定义 P0 artifact 输出规范。
- 当前 xiaocai 遇到的问题: 本地可产出，但跨实例可复用的 canonical projection 不稳定。
- 需要 FLARE 提供什么: 稳定的投影 contract 承载 artifacts/recommendations/evidence/process meta。
- 为什么不应在 instance 内解决: canonical contract 属于平台层，不应在 instance 私有化定义。
- 验收标准:
  1) contract 字段稳定且可版本化；
  2) 支持 instance 侧映射；
  3) 回归覆盖基础投影场景。
- 优先级: P0

## FLARE-TASK-004
- task_id: FLARE-TASK-004
- 标题: 通用 Schema / Validation 插件框架
- 背景: xiaocai 将新增本地校验脚本保证资产闭合。
- 当前 xiaocai 遇到的问题: 本地脚本可用但不可复用，难以跨实例共享。
- 需要 FLARE 提供什么: 通用 schema + validation 扩展框架。
- 为什么不应在 instance 内解决: 这是平台通用治理能力，不应由实例长期维护。
- 验收标准:
  1) 支持 schema 注册；
  2) 支持 validation 规则插件；
  3) 统一错误输出。
- 优先级: P1

## FLARE-TASK-005
- task_id: FLARE-TASK-005
- 标题: Pack Schema Version Compatibility 机制
- 背景: xiaocai 将引入新 `domain-packs` 结构并保留旧结构兼容。
- 当前 xiaocai 遇到的问题: 缺平台级 pack schema 版本协商与兼容策略。
- 需要 FLARE 提供什么: 版本协商机制与兼容策略（向后兼容、弃用窗口）。
- 为什么不应在 instance 内解决: 版本协商属于平台 contract 生命周期管理。
- 验收标准:
  1) 定义 pack schema 版本策略；
  2) 提供兼容检查入口；
  3) 对不兼容配置给出明确错误。
- 优先级: P1

## FLARE-TASK-006
- task_id: FLARE-TASK-006
- 标题: Recommendation Execution & Explanation Projection 标准化
- 背景: xiaocai 将新增推荐策略管理资产（时机/权重/模板池/禁用条件）。
- 当前 xiaocai 遇到的问题: 可在 instance 本地配置与计算推荐，但缺跨实例统一执行和解释投影标准。
- 需要 FLARE 提供什么: 推荐执行 hook（统一输入/输出/trace）+ 推荐解释 canonical projection。
- 为什么不应在 instance 内解决: 推荐执行与可解释输出是跨实例复用能力，若实例自定义将导致口径漂移。
- 验收标准:
  1) 支持基于规则权重执行推荐；
  2) 返回统一 explanation 字段（命中规则/权重/未命中条件）；
  3) 可被多个实例直接复用。
- 优先级: P1
