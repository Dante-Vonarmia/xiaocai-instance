# procurement-base v1

该目录表示标准采购领域 profile 的版本化落点。

当前处于兼容期：
- 实际入口仍由 `pack-registry/manifests/base-profiles.json` 指向 `domain-pack/*`。
- 后续 cutover 时迁入本目录并由 resolver 直接加载。

约束：
1. 不写入 tenant 私有数据。
2. 不复制 tenant 专属完整 pack。
