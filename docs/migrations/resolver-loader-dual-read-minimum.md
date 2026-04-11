# Resolver/Loader Dual-Read (Minimum Integration)

## 目标

在不改业务流程逻辑的前提下，为后续迁移提供最小接入规范：
1. resolver 可读取标准 profile 注册表。
2. loader 可按 tenant 配置合并 override。
3. 私有数据仅通过 bindings descriptor 挂载。

## 输入约定

1. Base profile registry
- 路径：`pack-registry/manifests/base-profiles.json`
- 关键键：`profile_id`, `version`, `entrypoints`

2. Tenant profile
- 路径：`tenant-config/tenants/<tenant_id>/profile.yaml`
- 关键键：`base_profile_id`, `overrides`, `bindings_ref`

3. Private bindings descriptor
- 路径：`bindings/*.yaml`
- 说明：只描述数据入口，不承载数据本体

## 最小加载顺序

1. `resolve_base_profile(base_profile_id, profile_version)`
- 从 registry 找到 profile
- 读取 profile entrypoints

2. `load_profile_assets(entrypoints)`
- 加载 schema / workflow / terminology / category / contracts / scenarios

3. `apply_tenant_overrides(overrides.files, merge_mode)`
- 仅合并 tenant 差异
- 不允许覆盖到 private data body

4. `attach_private_bindings(bindings_ref)`
- 加载 descriptor
- 在 runtime context 注入数据访问句柄（而非原始数据）

## 回退策略（兼容期）

当 registry 或 tenant 配置缺失时：
1. 允许回退到 `domain-pack` 旧入口。
2. 记录 warning（包含 tenant_id/base_profile_id）。
3. 不得静默降级为“随机默认配置”。

## 验收点

1. 同一 `base_profile_id` 可被多个 tenant 引用。
2. tenant 差异由 override 文件表达，不复制整套 pack。
3. 私有数据不出现在 profile/override 文件。
4. `scripts/pack-registry-check.sh` 可在 CI/本地作为前置校验。

## 不在本阶段实施

1. 不在产品层重写 FLARE resolver/runtime。
2. 不引入新编排引擎。
3. 不改变“需求梳理 -> 需求分析 -> RFX策略 -> 导出 -> 归档”流程。
