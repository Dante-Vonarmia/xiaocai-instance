# ADR-003 Product Profile vs Tenant Override

## Status

Accepted

## Date

2026-04-11

## Context

当前 `domain-pack` 同时承载了：
1. 标准采购领域模板。
2. 实例品牌/文案差异。
3. 与 tenant 私有数据相关的信息来源。

这会导致以下问题：
1. 随 tenant 增长出现“一客户一套 pack”的复制趋势。
2. 运行时边界模糊，容易把私有数据留在仓库配置层。
3. 与 FLARE 的 resolver/contract 职责重叠风险增加。

## Decision

采用三层模型：

1. Standard Product Profile（标准领域模板）
- 由 `pack-registry/` 维护。
- 使用 `profile_id + version` 管理。
- 数量应显著小于 tenant 数量。

2. Tenant Override（租户覆盖）
- 由 `tenant-config/` 维护。
- tenant 通过 `base_profile_id + overrides` 表达差异。
- 不复制完整 profile。

3. Tenant Private Data Bindings（租户私有数据绑定）
- 由 `bindings/` 仅保存绑定描述（descriptor）。
- 私有数据本体在数据库/对象存储/外部服务，不进入 repo。

## Non-Goals

1. 不重写 FLARE runtime / resolver / contract。
2. 不改变既有业务流程主链路：需求梳理 -> 需求分析 -> RFX策略 -> 导出 -> 归档。
3. 不在本次迁移中引入一套新的编排引擎。

## Consequences

正向影响：
1. 降低 tenant 扩展时的配置复制成本。
2. 明确配置层与数据层边界。
3. 降低 instance 层与 FLARE core 的职责冲突。

代价：
1. 需要 resolver/loader 支持 base profile + override 合并。
2. 需要迁移期双读（旧 `domain-pack` 与新 `pack-registry`）。

## Migration Rule

合并顺序固定为：
1. load base profile
2. apply tenant overrides
3. attach private data bindings at runtime

任何阶段都不得将 tenant 私有数据回写到 profile 文件。

## Current Execution Note (2026-04-29)

本 ADR 保留其三层模型决策，作为迁移与边界约束依据；
但当前实例仓默认执行基线已收敛为：

1. `domain-packs/` 作为领域资产主源
2. `tenant-config/` 作为 tenant overrides
3. `bindings/` 作为私有数据绑定描述

`pack-registry/` 已从当前实例仓删除，
不再作为默认运行时主链路或兼容层保留；除非后续出现明确的 profile 复用或独立 versioning 需求，否则不重新引入该层。
