# domain-packs (xiaocai P0)

本目录用于承载 xiaocai P0 场景的机器可读资产：
- xiaocai
- branding

状态：
- **Active / Source of Truth for new domain assets**
- FLARE 可加载的主业务包统一进入 `domain-packs/xiaocai/`
- legacy packs 已删除，不再作为历史场景资产或兼容参考保留在主仓库
- 主链路 source contract 见 `docs/contracts/xiaocai-domain-pack-source-contract.md`

约束：
- 仅承载 instance 领域资产
- 不包含 FLARE Core 主流程实现
- 所有临时绕行需记录到 docs/flare-dependency-gap-log.md
- logo、数据库、会员校验、auth 等实例运行配置不放入业务 domain pack

## Domain pack opt-in 口径

- xiaocai 主链路只读 `domain-packs/xiaocai/`；旧 `schema/`、`cards/`、`category-fields/`、`activity_procurement/`、`gift_customization/`、`shared/`、`contracts/`、`workflows/`、`terminology/` 不得恢复为主链路字段或 workflow 源。
- FLARE 不默认启用 generic domain pack；未显式配置 `domain_pack_domain` 时，不应展示任何 sub agent / module capability。
- `generic` 是显式 opt-in 开放基座，只有请求或环境显式指定 `domain_pack_domain=generic` 时才展示 generic 配置能力。
- `xiaocai` 是显式 opt-in 业务实例，xiaocai 请求必须携带：
  - `instance_id=xiaocai`
  - `domain_pack_domain=xiaocai`
  - `domain_pack_version=default`
- 当前 `domain-packs/xiaocai/` 只启用 `requirement_intake` 与 `analysis_mode`。
- 当前不启用 `intelligent_sourcing`；这表示未配置/未启用寻源模块，不是 UI 隐藏寻源。
- 前端和 instance app 不得本地补默认 module、不得从 generic 继承 module、不得按 tab/mode 猜能力；能力展示只能消费 backend 返回的 canonical `module_prompt_registry` / capability projection。
