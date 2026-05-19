# Permission Execution Checklist

Date: 2026-04-30

Related ADRs:

- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-005-collaboration-permission-layering.md`
- `/Users/dantevonalcatraz/Development/F.L.A.R.E/docs/adr/ADR-2026-04-30-authorization-capability-boundary.md`

## Purpose

本文件用于把权限分层 ADR 转成后续执行清单。

当前目标不是一次性完成完整协作权限体系，而是：

1. 先固定 xiaocai 的 scope / role / policy output contract
2. 再补 FLARE 的 capability hook
3. 最后接字段级权限与 patch/output filtering

---

## A. xiaocai Execution Checklist

### A1. P0 - Scope / Role / Policy Contract

1. 明确资源归属模型
   - `session`
   - `source`
   - `artifact`
   - `analysis result`
   - `supplier candidate`

2. 明确 scope contract
   - `personal`
   - `project`

3. 明确最小 member role contract
   - `owner`
   - `editor`
   - `viewer`

4. 明确 policy 输出结构
   - `visible_fields`
   - `masked_fields`
   - `readonly_fields`
   - `disabled_capabilities`
   - `reasons`

5. 固定 API 侧单一权限判定入口
   - 不允许 router 分散判断
   - 不允许 UI 自行补权限真相

### A2. P1 - Field / Capability Policy

6. 给关键对象补 field policy
   - `confirmed_fields`
   - `analysis.sections`
   - `supplier_candidates`

7. 给关键动作补 capability policy
   - `trigger_analysis`
   - `start_sourcing`
   - `export`
   - `start_rfp`

8. 给前端补 projection contract
   - `hidden`
   - `masked`
   - `readonly`
   - `disabled_reason`

---

## B. FLARE Execution Checklist

### B1. P0 - Capability Baseline

1. 补 scope primitive contract
   - `session_scope`
   - `project_scope`

2. 补 identity / auth context carrier

3. 补 authorization hook interface

4. 补 read filter hook

5. 补 write filter hook

6. 补 patch / output filter hook

### B2. P1 - Extension Points

7. 补 canonical output filter extension point

8. 补 patch filtering extension point

9. 补 capability enforcement hook

10. 补 instance policy decision 接入点

---

## C. Boundary Rules

### C1. xiaocai must not do

- 不把权限真相放前端
- 不把 field policy 写死在 UI
- 不把完整成员系统塞进 FLARE core

### C2. FLARE must not do

- 不写采购角色语义
- 不写预算 / 供应商 / 策略字段权限
- 不写谁能发起 RFP 这类 instance 业务规则

---

## D. Recommended Order

1. xiaocai 先补 `scope + role + policy output contract`
2. API 固定单一判权入口
3. 前端只消费 projection
4. FLARE 再补 capability hook
5. 最后接字段级 filtering 与 patch/output filtering

---

## E. Delivery Notes

当前阶段建议按以下口径执行：

1. 先完成 contract 和入口收口
2. 再做最小 project 协作权限
3. field-level 权限晚于 scope / role / capability 基线
4. domain-specific policy 始终留在 xiaocai instance
5. FLARE 仅补 capability，不补小采规则

---

## F. Chat 状态连续性执行检查（2026-05-19）

目的：在“上下文疑似丢失/回复机械化”场景下，先做链路检查与确认记录，再允许进入代码修改。

### F1. 必检项（上线前与问题复盘都要执行）

1. Session 连续性
   - 同一轮对话是否持续写入同一 `session_id`。
   - 若 session 漂移，先修 session 接入层，不进入策略层修改。

2. 消息持久化完整性
   - 用户/助手回合是否完整落库（按 created_at 连续）。
   - 确认不是“前端显示有、后端未写入”。

3. 字段承接能力
   - 对“crm/erp/oa”等短回复，是否能承接到采购字段（如 `产品/服务`）。
   - 若不能，记录为 extractor 承接缺口。

4. 分流优先级
   - 用户明确“直接给方案”时，是否仍被强制追问门控覆盖。
   - 若覆盖，记录为策略优先级问题（而非模型记忆问题）。

5. 回滚准备
   - 所有修复必须有开关或可回退变更点。
   - 灰度观察指标：重复追问率、短回复承接率、方案直出率。

### F2. 本次确认记录（已确认，未改代码）

- 记录日期：2026-05-19
- 问题会话：`sess_c75cadf26f92`
- 已确认事实：
  - 消息在同一 session 连续落库（非会话丢失）。
  - 现象为“状态承接弱 + 追问门控覆盖语义”，导致用户感知为“记不住上下文”。
- 决策：
  - 先完成文档排期与评审记录，再进入最小代码修复。
- 状态：
  - 文档排期已确认；代码修改未开始。

### F3. 最小修复方案（评审稿，未实施）

范围边界（必须遵守）：
- 只修 chat 状态承接与分流，不做架构重构。
- 不修改 FLARE kernel 边界；仅在 xiaocai adapter 层最小补强。
- 所有改动必须可回滚。

拟实施项（按优先级）：
1. 短回复字段承接补强（P0）
   - 目标：`crm/erp/oa/bi` 等短回复可承接到 `产品/服务` 等最小字段。
   - 预期：降低“你要采购什么”重复追问。

2. “直接给方案”分流优先级（P0）
   - 目标：当用户明确要求先给方案时，输出“初版方案 + 待确认清单”，避免被纯追问覆盖。
   - 预期：降低机械化回复，提高可执行输出率。

3. 最近轮次状态回填（P1，可开关）
   - 目标：回填最近 N 轮结构化状态信号，降低单轮抽取波动影响。
   - 预期：提升连续多轮稳定性。

### F4. 实施排期（确认版）

- D0（2026-05-19）：
  - 完成证据确认与排期冻结（已完成）。
- D1：
  - 输出代码改动清单与回滚点（不改代码）。
  - 完成评审通过记录（产品/后端/测试）。
- D2：
  - 实施 P0 最小修复（短回复承接 + 直接给方案分流）。
- D3：
  - 回归测试 + 灰度观察（重复追问率、短回复承接率、方案直出率）。
- D4：
  - 是否全量发布决策与上线确认记录。

### F5. 回答+导航双通道检查（产品策略）

目的：避免“只追问、无全貌”的机械感，同时不操纵模型判断结果。

1. 回答通道（Answer Channel）
   - 约束：不得重写模型核心结论，不得伪造已确认事实。
   - 允许：在结果为空或不完整时输出 `v0` 草案并标注待确认项。

2. 导航通道（Navigation Channel）
   - 必需字段：
     - `current_stage`
     - `stage_progress`
     - `confirmed_summary`
     - `missing_summary`
     - `next_best_action`
   - 展示目标：用户每轮都能看见“现在到哪一步、还差什么”。

3. 执行检查
   - 不因导航通道覆盖回答通道真实结果。
   - 不把前端投影当作后端 authoritative state。
   - 策略变更需可回滚（配置回退或分支回退）。

4. 验收场景
   - 场景 A：短回复（如 crm）后，导航通道应更新“已确认信息”。
   - 场景 B：用户要求“直接给方案”时，回答通道可给 `v0`，导航通道同步给待确认清单。
   - 场景 C：连续多轮后，导航通道阶段应单调推进或明确停滞原因。
