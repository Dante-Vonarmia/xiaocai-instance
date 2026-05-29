# 第2章 Domain Pack Context

## 2.1 定义

Domain Pack Context 是 xiaocai 注入 FLARE 的采购领域上下文集合。  
它不是 prompt 散文，而是可校验、可挂载、可追溯的结构化资产。

## 2.1.1 最新 opt-in 口径

FLARE 不再默认启用 generic domain pack。未显式配置 `domain_pack_domain` 时，backend canonical `module_prompt_registry` 应为空，前端不应展示任何 sub agent / module capability。

Domain pack 只通过显式 opt-in 生效：

| 请求 / 会话配置 | 预期能力投影 |
|---|---|
| 未传 `domain_pack_domain` | `module_prompt_registry=[]` |
| `domain_pack_domain=generic` | 展示 generic 配置的全部能力：`requirement_intake`、`analysis_mode`、`intelligent_sourcing` |
| `domain_pack_domain=xiaocai` | 只展示 xiaocai 当前启用能力：`requirement_intake`、`analysis_mode` |

xiaocai instance 转发给 FLARE 的请求必须显式携带：

```json
{
  "instance_id": "xiaocai",
  "domain_pack_domain": "xiaocai",
  "domain_pack_version": "default"
}
```

当前 xiaocai domain pack 不启用 `intelligent_sourcing`。这不是“隐藏寻源”，而是当前 `xiaocai` pack 未配置/未启用寻源模块；UI 不得本地补默认模块、不得从 `generic` 继承模块、不得根据 tab/mode 猜能力。

## 2.2 当前资产来源

| 内容 | 文件 |
|---|---|
| 字段总表 | `domain-packs/xiaocai/fields.yaml` |
| workflow / module registry / policy | `domain-packs/xiaocai/workflow.yaml` |
| 品类目录与 intent aliases | `domain-packs/xiaocai/taxonomy.yaml` |
| 替换与 reconciliation 规则 | `domain-packs/xiaocai/replace-rules.yaml` |
| 搜索映射 | `domain-packs/xiaocai/search-mapping.yaml` |
| 输出模板 | `domain-packs/xiaocai/templates/` |

主链路 source contract 见：

```text
docs/contracts/xiaocai-domain-pack-source-contract.md
```

历史 `domain-packs/schema/`、`activity_procurement/`、`gift_customization/`、`shared/` 可作为参考或迁移输入，但不得驱动当前 xiaocai 主链路。

## 2.3 调整原则

1. 新关键词优先进入 `terminology/procurement.yaml`。
2. 新品类优先进入 `category-fields/procurement-category-fields.yaml`。
3. 新字段必须能在字段总表或场景字段中闭合。
4. 新补问逻辑优先进入对应 `question_flow.yaml`。
5. 不在 route、UI、FLARE Core 中硬编码采购字段。

## 2.4 验证命令

```bash
diff -qr /Users/dantevonalcatraz/Development/F.L.A.R.E/domain-packs/xiaocai /Users/dantevonalcatraz/Development/procurement-agents/domain-packs/xiaocai
./scripts/verify-xiaocai-launch.sh
```

## 2.5 联调输出

下周联调时，domain context 至少要能输出：

1. matched taxonomy：一级/二级品类。
2. matched terminology：命中的采购关键词或同义词。
3. field policy：当前阶段 required/recommended/missing fields。
4. next action hints：继续补字段、进入分析、进入 RFX；寻源仅在后续显式启用对应 domain pack module 后出现。
