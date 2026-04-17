# Pack Registry

本目录用于维护“少量标准领域模板（base profiles）”，不再采用“一客户一套完整 pack”。

职责边界（强约束）：
- `pack-registry/` 只维护 profile 索引与入口清单（manifest/metadata）
- 不承载 tenant overrides
- 不承载 tenant private data
- 不直接承载具体业务领域资产正文（资产正文位于 `domain-packs/`）

## 目标

1. 标准 profile 数量应显著小于 tenant 数量。
2. tenant 差异通过 `tenant-config` 的 overrides 表达。
3. tenant 私有数据通过 `bindings` 与数据层绑定，不进入 profile 文件。

## 校验入口

执行：

```bash
bash scripts/pack-registry-check.sh
```

或在 `deploy/` 下执行：

```bash
make pack-registry-check
```
