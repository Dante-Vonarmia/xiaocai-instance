# Domain Pack to Pack Registry Migration

> Status note (2026-04-29):
> 本文档保留为历史迁移方案说明。
> 当前仓库默认执行基线已收敛为 `domain-packs + tenant-config + bindings`；
> `pack-registry` 目录已删除，不再作为默认运行时主链路。

## Scope

将当前 `domain-pack` 从“实例配置包”收口到：
1. `pack-registry`（标准 profile 注册）
2. `tenant-config`（tenant 覆盖）
3. `bindings`（私有数据绑定描述）

## Mapping

| Current | Target | Action |
|---|---|---|
| `domain-pack/schema/*` | `pack-registry/profiles/<profile>/v<version>/schema/*` | 保留为标准 profile |
| `domain-pack/workflows/*` | `pack-registry/profiles/<profile>/v<version>/workflows/*` | 保留为标准 profile |
| `domain-pack/contracts/procurement-*.yaml` | `pack-registry/profiles/<profile>/v<version>/contracts/*` | 保留为标准 profile |
| `domain-pack/contracts/scenarios/*` | `pack-registry/profiles/<profile>/v<version>/scenarios/*` | 保留为标准 fixture |
| `domain-pack/category-fields/*` | `pack-registry` + `tenant-config/overrides` | 主干保留，差异下沉 override |
| `domain-pack/terminology/*` | `pack-registry` + `tenant-config/overrides` | 主干保留，差异下沉 override |
| `domain-pack/cards/*` | `tenant-config/overrides` (优先) | 租户展示差异下沉 |
| `domain-pack/branding/*` | `tenant-config/overrides` | 明确归入 tenant override |
| `domain-pack/contracts/flare-contract-mapping.yaml` | FLARE contract/resolver 对齐文档 | 不在产品层扩展 core contract |
| `docs/discussions/*.csv` 中私有样本 | 外部数据层 + `bindings/*` descriptor | 从 repo 配置层移出 |

## Phases

### Phase 0: Compatibility Bootstrap

1. 新增 `pack-registry/manifests/base-profiles.json`。
2. 入口先指向现有 `domain-pack` 文件，保证运行不受影响。
3. 新增 tenant/profile schema 与 migration 文档。

### Phase 1: Dual Read

1. resolver 支持同时读取：
- `pack-registry` 主入口
- 旧 `domain-pack` 兼容入口
2. tenant 配置通过 `base_profile_id + overrides + bindings_ref` 生效。

### Phase 2: Cutover

1. 将标准 profile 文件迁移至 `pack-registry/profiles/...`。
2. `domain-pack` 保留只读快照并标注 deprecated。
3. 清理 tenant 私有数据在仓库存量。

## Acceptance Checklist

1. 标准 profile 数量显著小于 tenant 数量。
2. tenant 不再复制完整 pack。
3. 私有数据不在 repo 配置层长期存放。
4. 与 FLARE resolver/loader 契约对齐，不在产品层重造 runtime。

## Related

- `docs/migrations/resolver-loader-dual-read-minimum.md`
