# ADR-004 Instance API Execution Baseline

## Status

Accepted

## Date

2026-04-30

## Context

针对 xiaocai instance API 当前能力盘点，已明确以下现实状态：

1. API 自身存储层、kernel 调用链、domain-packs 读取链路已经具备基础闭环。
2. 成员/人员体系目前只具备最小 project access 与 ownership 能力，尚未完成完整成员管理闭环。
3. 当前版本需要优先完成 instance API 自身能力，而不是继续等待更完整的 domain-pack canonical 注入设计。
4. domain-pack 注入方式、canonical 口径、与 kernel 的最终边界设计仍未最终确定。

本 ADR 用于记录 2026-04-30 当天确认的执行口径，避免后续实现阶段继续摇摆。

## Decision

### 1. Database Baseline

xiaocai instance API 的数据库接口统一以 **PostgreSQL** 作为标准目标。

执行口径：

- PostgreSQL 是默认、正式、统一的数据存储接口。
- SQLite 兼容能力不作为当前阶段的目标收口标准。
- 后续 API 能力补全、成员能力补全、配置能力补全，均以 PostgreSQL 为准进行验证。

### 2. Membership / Personnel Scope

成员/人员相关“不满足的部分”属于 **明确要做的范围内工作**，不是当前阶段的非目标。

执行口径：

- 当前最小 ownership / project_members 能力可以作为过渡基线继续使用。
- 仍需继续补完成员管理所需接口与数据能力。
- 后续实现可以包括但不限于：project member 管理、角色更新、成员列表、可见性/写权限补齐。

### 3. API Ownership

xiaocai instance API 可以继续按“**自己重写并补全**”的方式推进，这一方向本身没有问题。

执行口径：

- API 层由 xiaocai instance 自己承接，不以“尽量不碰现有 API”作为约束。
- 可继续替换、补齐、重组当前 API 能力，只要边界仍保持在 instance application / storage / adapter 范围内。
- kernel 仍作为外部能力边界；xiaocai API 自己负责 instance 侧权限、状态、存储、工作流拼装与投影。

### 4. Domain-Pack Injection Timing

domain-pack 注入在当前版本 **不作为阻塞项**。

执行口径：

- 当前版本允许先不完成完整 domain-pack 注入。
- 也允许将其作为稍后阶段的延后项处理。
- 在 canonical 注入方式、注入时机、kernel 输入边界尚未明确前，不强行落地半成品方案。
- 当前阶段保留 `domain-packs` 读取 / 挂载 / 配置资产能力即可。

## Non-Goals

当前阶段不要求完成：

1. domain-pack canonical 注入协议最终版。
2. domain-pack 注入与 kernel 之间的最终 contract freeze。
3. 成员体系之外的额外组织架构扩展设计。

## Execution Window

目标执行窗口为：

- **2026-05-04 至 2026-05-10**

即在 **Monday, May 4, 2026** 开始的一周内，尽量完成以下收口：

1. PostgreSQL 作为 instance API 统一数据库接口的收口与验证。
2. 成员/人员相关缺口的继续补全。
3. API 自身能力补全与必要重写。
4. domain-pack 注入继续保持延后，不阻塞本轮交付。

## Consequences

正向影响：

1. 先把 instance API、数据库、成员能力收口，减少并行设计带来的分散。
2. 避免在 domain-pack canonical 注入方案未成熟前过早固化错误边界。
3. 明确当前阶段的重点是“API 可交付”和“成员能力补齐”，不是抽象设计完备性。

代价：

1. domain-pack 注入能力会在当前版本中暂时不完整。
2. 后续仍需补一轮关于 canonical 注入与 kernel 边界的正式设计。
3. 当前阶段对 SQLite/兼容路径的投入应显著降低。
