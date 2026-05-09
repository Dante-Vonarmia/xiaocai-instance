# 第2章 Domain Pack Context

## 2.1 定义

Domain Pack Context 是 xiaocai 注入 FLARE 的采购领域上下文集合。  
它不是 prompt 散文，而是可校验、可挂载、可追溯的结构化资产。

## 2.2 当前资产来源

| 内容 | 文件 |
|---|---|
| 字段总表 | `domain-packs/schema/procurement-field-dictionary.yaml` |
| 阶段字段集 | `domain-packs/schema/procurement.yaml` |
| 品类目录 | `domain-packs/category-fields/procurement-category-fields.yaml` |
| 术语/关键词 | `domain-packs/terminology/procurement.yaml` |
| 活动场景字段 | `domain-packs/activity_procurement/fields.yaml` |
| 礼品场景字段 | `domain-packs/gift_customization/fields.yaml` |
| 推荐策略 | `domain-packs/shared/rules/recommendation_policy_registry.yaml` |

## 2.3 调整原则

1. 新关键词优先进入 `terminology/procurement.yaml`。
2. 新品类优先进入 `category-fields/procurement-category-fields.yaml`。
3. 新字段必须能在字段总表或场景字段中闭合。
4. 新补问逻辑优先进入对应 `question_flow.yaml`。
5. 不在 route、UI、FLARE Core 中硬编码采购字段。

## 2.4 验证命令

```bash
python3 scripts/validate_domain_packs.py
python3 -m unittest discover -s tests/domain_packs -p 'test_*.py' -v
```

## 2.5 联调输出

下周联调时，domain context 至少要能输出：

1. matched taxonomy：一级/二级品类。
2. matched terminology：命中的采购关键词或同义词。
3. field policy：当前阶段 required/recommended/missing fields。
4. next action hints：继续补字段、进入分析、进入寻源、进入 RFX。
