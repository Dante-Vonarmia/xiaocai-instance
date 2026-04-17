# Tenant Config

本目录仅存放 tenant 侧配置，不存放完整领域模板。

职责边界（强约束）：
- `tenant-config/` 只存放 tenant 级 overrides
- 所有 tenant 必须引用 `base_profile_id`（由 `pack-registry/` 管理）
- tenant 私有数据只通过 `bindings_ref` 间接引用，私有数据正文不得入库本目录

每个 tenant 配置必须：
1. 指向一个 `base_profile_id`。
2. 通过 overrides 表达差异。
3. 通过 `bindings_ref` 引用私有数据绑定描述。

禁止将 tenant 私有业务数据直接写入 profile/override 文件。
