# ADR-005 Collaboration Permission Layering

## Status

Accepted

## Date

2026-04-30

## Context

xiaocai 当前主流程以 **会话（session）** 为核心执行单位：

1. 每一条需求梳理、需求分析、智能寻源都在会话上下文中完成。
2. 当前默认采用 **单用户隔离模型**：
   - 每个用户的数据、会话、结果完全隔离
   - 不存在跨用户访问或共享

但产品演进方向已经明确：

1. 后续会进入 **Project 协作模型**
   - 一个项目下允许多个成员参与
   - 会话不再只属于个人，而是属于项目
   - 多个成员可见同一条会话、分析结果、寻源结果
2. 再进一步会进入 **细粒度权限控制**
   - 字段级可见性（field-level visibility）
   - 能力级可用性（capability-level access）
   - 编辑权限与操作权限差异

例如：

- 预算字段只允许管理角色可见
- 供应商名单只允许部分成员可见
- 分析结论全员可见
- 某些成员可查看但不可编辑
- 某些成员可查看但不可触发分析 / 发起 RFP

当前需要先固定的不是最终规则细节，而是 **这些权限能力与语义应该落在哪一层**。

## Decision

### 1. FLARE 只负责权限能力，不负责小采业务权限规则

FLARE 侧只应提供通用 capability，不承载 xiaocai 的业务权限语义。

FLARE 适合提供：

- session scope / project scope primitive
- identity / auth context carrier
- authorization hook interface
- read / write filter interface
- patch / output filtering capability
- policy evaluation extension point

FLARE 不应承载：

- 小采 project/member 业务语义
- 采购角色定义（采购 / 管理 / 需求方）
- 预算、供应商、策略等字段权限规则
- 谁可以发起分析 / 发起 RFP / 查看供应商等业务策略

### 2. xiaocai instance 负责真正的权限语义与策略

以下内容必须定义在 xiaocai instance：

- project 概念
- project member / role 语义
- 字段级权限规则
- 能力级权限规则
- 数据可见性规则
- 编辑权限 / 操作权限规则

也就是说：

- FLARE 提供 mechanism
- xiaocai 定义 policy

### 3. 字段级权限的真实归属是 Field Policy / Data Contract 层

在 xiaocai 中，权限最终会落到具体数据对象与输出结构上。

首批关键对象包括但不限于：

- `confirmed_fields`
- `analysis.sections`
- `supplier_candidates`

因此，权限问题不仅是“能否访问会话”，更是：

- 会话中的哪些字段可见
- 哪些 section 可见
- 哪些能力可用
- 哪些 patch / output 需要过滤或降级

### 4. UI 只做 projection，不做真实权限判定

UI 可以做：

- hidden / masked / readonly / disabled 投影
- unavailable reason 展示

UI 不可以做：

- 自己发明 authoritative permission truth
- 用前端临时逻辑替代后端权限结论

## Current Baseline

在当前阶段：

1. 继续保持 **单用户隔离模型** 作为默认基线。
2. project 协作模型作为后续演进方向。
3. 字段级 / 能力级权限作为后续阶段的明确目标，但不要求本周先完成最终实现。

## Layering Rule

冻结如下三层分工：

### Scope Layer

负责资源归属范围：

- personal session
- project session
- resource ownership / project ownership

该层是 capability / contract 层，不承载具体采购权限语义。

### Policy Layer

负责具体业务权限规则：

- role -> field visibility
- role -> capability access
- role -> write permission

该层属于 xiaocai instance。

### Projection Layer

负责将权限结果投影到 UI：

- hidden field
- masked field
- readonly section
- disabled action

该层不拥有真权限，只消费后端判定结果。

## Non-Goals

当前 ADR 不定义：

1. 最终角色集合与角色命名。
2. 每个字段的最终权限矩阵。
3. 最终 patch filtering contract 字段设计。
4. 与 kernel 的最终 canonical 注入协议。

## Consequences

正向影响：

1. 明确权限语义不进入 FLARE core。
2. 避免 UI 过早承担真实权限逻辑。
3. 为后续 project 协作和字段级权限演进保留清晰边界。

代价：

1. 后续仍需在 xiaocai instance 中补完整的 policy contract。
2. 后续仍需在 FLARE 中补 capability hook，而不是直接写规则。
3. 字段级权限设计会推迟到 project 协作模型更明确之后再细化。

## Related

- `/Users/dantevonalcatraz/Development/procurement-agents/docs/adr/ADR-004-instance-api-execution-baseline.md`
- FLARE repo 对应平台侧 ADR：`ADR-2026-04-30-authorization-capability-boundary.md`
