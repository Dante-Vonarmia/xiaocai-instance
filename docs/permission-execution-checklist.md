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
