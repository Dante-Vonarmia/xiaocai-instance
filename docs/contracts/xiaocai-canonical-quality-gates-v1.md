# xiaocai canonical quality gates v1

## 1. 目的

本文件冻结 xiaocai 侧交给 FLARE 消费的质量门禁口径：

1. 数据契约字段与别名必须闭合。
2. 品类字段必须能驱动完整追问。
3. readiness / 字段权重算法必须稳定可验收。
4. 分析模板必须有字段依赖。
5. xiaocai 不实现运行时功能，真实追问、状态推进、canvas/stream 输出由 FLARE 执行。

## 2. 非目标

1. 不在 xiaocai 新增 workflow engine。
2. 不在 xiaocai 新增追问 runtime。
3. 不在 xiaocai 新增 stream / canvas / pending contract 功能。
4. 不把 router / UI 作为 authoritative state owner。
5. 不修改 FLARE kernel contract。

## 3. 字段 source 与别名门禁

字段总表基线：

- 当前 Excel：`/Users/dantevonalcatraz/Downloads/数据契约和测试/数据契约20260411.xlsx#总字段表`
- xiaocai 字段表：`domain-packs/schema/procurement-field-dictionary.yaml`
- 字段数量：81

已核对门禁：

| 项 | 预期 |
|---|---|
| Excel 字段数 | 81 |
| YAML 字段数 | 81 |
| 需求梳理必填集 | 14 |
| 需求分析必填集 | 17 |
| RFX策略必填集 | 33 |

必须显式闭合的别名 / 派生字段：

| 外部/业务说法 | canonical 字段 | 类型 | gate 策略 |
|---|---|---|---|
| 数量和单位 | 数量 + 单位 | split | 影响需求梳理 readiness |
| 影响范围 | 影响范围（部门/区域） | alias | 不阻断，影响分析质量 |
| 供应商数量 | 候选数量 | alias | 影响寻源完整性，不阻断需求梳理 |
| 交期时长 | 交付时间 / 响应时效 | derived | 影响寻源完整性 |
| 注册资金 | 注册资本 | alias | 影响供应商筛选 |
| 成立时长 | 成立日期 / 成立年份 | derived | 影响供应商筛选 |
| 对标企业 | deferred placeholder | optional placeholder | 不作为 v1 readiness gate |
| 员工规模 | deferred placeholder | optional placeholder | 不作为 v1 readiness gate |
| 实缴资金 | deferred placeholder | optional placeholder | 不作为 v1 readiness gate |
| 企业性质 | deferred placeholder | optional placeholder | 不作为 v1 readiness gate |
| 社保人数 | deferred placeholder | optional placeholder | 不作为 v1 readiness gate |

机器可读位置：

- `domain-packs/schema/procurement-field-dictionary.yaml#field_aliases`

## 4. 品类字段矩阵 contract

品类字段矩阵基线：

- 当前 Excel：`/Users/dantevonalcatraz/Downloads/数据契约和测试/数据契约20260411.xlsx#品类维度的需求处理`
- xiaocai 品类目录：`domain-packs/category-fields/procurement-category-fields.yaml`
- 采购负责类数量：10
- 一级品类数量：45
- 二级品类数量：96

v1 使用 `field_matrix_defaults` 作为所有品类路径的基础字段矩阵：

| 字段组 | 用途 |
|---|---|
| `required_fields` | 驱动最小追问与核心 readiness |
| `recommended_fields` | 提升分析 / 寻源质量 |
| `optional_fields` | 作为补充上下文，不阻断 |

机器可读位置：

- `domain-packs/category-fields/procurement-category-fields.yaml#field_matrix_defaults`

## 5. canonical readiness 输入

FLARE 执行时应只依赖 xiaocai 输出的 contract 信号，不依赖 xiaocai runtime 推断。

最小输入：

1. `current_stage`
2. `resolved_category`
3. `confirmed_fields`
4. `missing_fields`
5. `field_weights`
6. `hard_blockers`
7. `analysis_template_dependencies`
8. `sourcing_output_template_dependencies`

## 6. 字段权重算法

### 6.1 字段分组

| 分组 | 含义 | 默认权重池 |
|---|---|---:|
| core_required | 当前阶段数据契约必填字段 | 60 |
| category_required | 命中品类后必须补齐的品类字段 | 25 |
| quality_recommended | 提升分析/寻源质量但不阻断的字段 | 15 |

每个字段在本组内等权。  
若某组没有字段，该组权重按比例分摊到剩余组，不产生空权重。

### 6.2 readiness 计算

```text
readiness_score =
  confirmed_core_required_weight
  + confirmed_category_required_weight
  + confirmed_quality_recommended_weight
```

分数范围：`0.0` 到 `1.0`。

字段确认标准：

1. 字段存在于 `confirmed_fields`。
2. 值不是空字符串、空数组、空对象或 null。
3. split / alias / derived 字段必须写入 `field_history` 或等价 trace。

### 6.3 阈值

| 状态 | 条件 | FLARE 行为期望 |
|---|---|---|
| blocked | 存在 hard blocker | 继续追问，不进入最终分析 |
| collecting | `readiness_score < 0.60` | 继续追问核心字段 |
| draft_ready | `readiness_score >= 0.60` 且无 hard blocker | 可生成草稿，不可最终确认 |
| analysis_ready | `readiness_score >= 0.80` 且 core/category required 完成 | 可进入需求分析 |
| final_ready | `readiness_score >= 0.95` | 可输出确认态分析 / RFX 文档 |

## 7. hard blocker

v1 hard blocker 只允许来自 contract，不允许由 UI 或 router 临时推断。

需求梳理 hard blocker：

1. `采购目的` 缺失。
2. `使用场景` 缺失。
3. `一级品类` 和 `二级品类` 都无法确认。
4. `预算金额`、`交付时间`、`交付地点` 同时缺失两个及以上。

需求分析 hard blocker：

1. 需求梳理 hard blocker 未解除。
2. `产品/服务 说明` 缺失且品类字段不足。
3. `质量标准` 和 `验收口径` 同时缺失。

寻源 hard blocker：

1. `一级品类` 或 `二级品类` 缺失。
2. `产品/服务` 缺失。
3. `交付地点` 缺失。

## 8. 输出模板 contract

需求分析模板必须覆盖 7 段：

1. 项目理解与核心需求
2. 市场现状和分析
3. 成本结构分析
4. 项目风险分析
5. 采购策略分析
6. 供应商选择建议
7. 项目实施计划与执行建议

每段必须声明：

1. `section_id`
2. `title`
3. `required_fields`
4. `optional_fields`
5. `block_on_missing_required`
6. `draft_allowed_when_missing`

机器可读位置：

- `domain-packs/contracts/procurement-analysis-rfx-templates.yaml#analysis_template`

智能寻源输出模板必须覆盖 5 段：

1. 输入约束摘要
2. 候选池说明
3. 推荐理由
4. 风险提示
5. 下一步动作

每段必须声明字段依赖与缺字段策略。

机器可读位置：

- `domain-packs/contracts/procurement-search-sourcing-replace.yaml#sourcing_output_template`

## 9. 验收 fixture 要求

每个真实采购 case 至少声明：

1. 初始用户输入。
2. 期望命中的一级/二级品类。
3. 期望缺失字段列表。
4. 期望下一轮追问字段。
5. 期望 readiness 分数区间。
6. 是否允许进入分析。
7. 期望分析模板段落。

机器可读位置：

- `domain-packs/contracts/scenarios/*.yaml`

## 10. 最小验收命令

```bash
python3 scripts/validate_domain_packs.py --root domain-packs
./.venv/bin/pytest adapters/http_api/tests/test_chat_prior_context.py adapters/http_api/tests/test_chat_workbench_projection.py tests/domain_packs -q
./.venv/bin/pytest adapters/http_api/tests/test_chat_stream_text.py adapters/http_api/tests/test_chat_stream_projection.py -q
```

## 11. FLARE handoff 口径

xiaocai 交付给 FLARE 的是：

1. 字段字典。
2. 别名 / 派生映射。
3. 品类字段矩阵。
4. readiness / hard blocker contract。
5. 分析模板 contract。
6. 寻源输出模板 contract。
7. 验收 fixture。
8. 最小验收命令。

FLARE 负责：

1. 使用上述 contract 进行追问。
2. 推进 canonical state。
3. 输出 canvas / stream / pending compatibility projection。
4. 执行真实分析生成。
