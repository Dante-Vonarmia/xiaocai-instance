# xiaocai domain-pack source contract（锁版）

更新时间：2026-05-29

## 1. Scope

本文固定 xiaocai instance 与 FLARE 对齐时的 domain-pack 源头、请求接口、加载边界和验收口径。

本文只定义 xiaocai domain-pack 作为配置资产如何被 xiaocai instance 读取并转交给 FLARE；不定义 FLARE kernel/runtime 的内部实现。

## 2. Source of Truth

xiaocai 主链路唯一 domain-pack source of truth：

```text
domain-packs/xiaocai/
  fields.yaml
  workflow.yaml
  taxonomy.yaml
  replace-rules.yaml
  search-mapping.yaml
  templates/
```

该目录必须与当前 FLARE 测试环境的 `domain-packs/xiaocai/` 保持一致。

以下 legacy pack 目录已从主仓库删除，不得恢复为历史资产、参考材料、迁移输入或主链路 fallback：

```text
domain-packs/schema/
domain-packs/cards/
domain-packs/category-fields/
domain-packs/activity_procurement/
domain-packs/gift_customization/
domain-packs/shared/
domain-packs/contracts/
domain-packs/workflows/
domain-packs/terminology/
```

例外：logo、branding、公司信息、认证、数据库连接等 instance 运行配置不属于业务 domain-pack，可保留在对应 instance config。

## 3. xiaocai -> FLARE request interface

xiaocai instance 调用 FLARE 时必须显式携带：

```json
{
  "instance_id": "xiaocai",
  "domain_pack_domain": "xiaocai",
  "domain_pack_version": "default"
}
```

允许出现在 request envelope 或 payload/context 的等价位置，但 xiaocai adapter 必须保证进入 FLARE 的最终请求可解析出以上三项。

## 4. Capability projection contract

能力展示以 FLARE backend canonical projection 为准。

当前 xiaocai pack 启用的 module capability：

```text
requirement_intake
analysis_mode
```

当前 xiaocai pack 不启用：

```text
intelligent_sourcing
```

约束：

1. 前端不得本地补默认 module。
2. xiaocai instance 不得从 `generic` pack 继承 module。
3. UI 不得根据 tab、mode、历史默认值猜 capability。
4. `intelligent_sourcing` 不出现表示当前 pack 未启用，不是 UI 隐藏。

## 5. Loader boundary

xiaocai `contract_loader` 只能读取 `domain-packs/xiaocai/`。

允许：

1. 解析 `fields.yaml` / `workflow.yaml` / `taxonomy.yaml` / templates。
2. 将字段、模板、taxonomy、module registry 映射为 FLARE 输入或 xiaocai 展示投影。
3. 保留 adapter 外部字段，例如 workflow 中 `adapter_authoritative_when_available` 指向的 provider 字段。

禁止：

1. 回退读取 `domain-packs/schema/*` 或任何已删除 legacy pack 作为主链路字段源。
2. 从历史场景 pack 合并字段或规则。
3. 在 xiaocai 本地执行 domain-pack runtime、readiness runtime、question planning runtime 或 workflow engine。
4. 用 domain-pack 直接覆盖 FLARE canonical state。
5. 由 UI 或 route 根据 domain-pack 反推 authoritative state。

## 6. Patch / writeback boundary

FLARE 是 patch、canonical state、workflow projection、composer UI、analysis payload 的主语义 owner。

xiaocai instance 只做：

1. request envelope 兼容。
2. FLARE patch/action/writeback 透传和必要 shape mapping。
3. session/message 持久化。
4. xiaocai workbench 展示投影。

xiaocai instance 不得：

1. 伪造 `next_actions`。
2. 把 legacy interaction payload 升级成主问题。
3. 把 observation 字段当 authoritative state。
4. 本地新建 analysis/sourcing/artifact runtime。

## 7. Sync check

与本地 FLARE repo 对齐时执行：

```bash
./scripts/check-xiaocai-pack-sync.sh
```

预期：输出 aligned。

如需从 FLARE repo 同步：

```bash
rsync -a --delete \
  /Users/dantevonalcatraz/Development/F.L.A.R.E/domain-packs/xiaocai/ \
  /Users/dantevonalcatraz/Development/procurement-agents/domain-packs/xiaocai/
```

同步后必须跑：

```bash
./scripts/verify-xiaocai-launch.sh
```

## 8. Regression anchors

当前测试必须固定以下口径：

1. `domain-packs/xiaocai/fields.yaml` 字段定义数量为 81。
2. `taxonomy.intent_aliases` 不把 `寻源` / `供应商` 直接 alias 到 `intelligent_sourcing`。
3. `workflow.module_prompt_registry` 只启用 `requirement_intake` 与 `analysis_mode`。
4. `requirements-document.md` 保留 FLARE 测试口径的需求梳理输出结构。
5. legacy interaction payload 不得触发 xiaocai 主问题。
6. 本地 adapter 不得自动补 `next_actions` fallback。

## 9. Rollback

若 FLARE 测试环境 domain-pack 更新后引入不兼容，回滚点是：

```text
domain-packs/xiaocai/
adapters/http_api/tests/test_xiaocai_domain_config.py
```

不得通过恢复旧 `schema/*`、旧场景 pack 或 UI fallback 来绕过不兼容。
