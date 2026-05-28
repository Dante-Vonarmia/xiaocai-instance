# domain-packs (xiaocai P0)

本目录用于承载 xiaocai P0 场景的机器可读资产：
- xiaocai
- shared
- activity_procurement
- gift_customization

状态：
- **Active / Source of Truth for new domain assets**
- FLARE 可加载的主业务包统一进入 `domain-packs/xiaocai/`
- `activity_procurement`、`gift_customization` 保留为历史场景资产/兼容参考，不得驱动主流程

约束：
- 仅承载 instance 领域资产
- 不包含 FLARE Core 主流程实现
- 所有临时绕行需记录到 docs/flare-dependency-gap-log.md
- logo、数据库、会员校验、auth 等实例运行配置不放入业务 domain pack
