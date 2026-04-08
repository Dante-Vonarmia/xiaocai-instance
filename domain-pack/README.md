# xiaocai Domain Pack

xiaocai 采购领域配置包（Sheet1 + Sheet3 首轮基线）- 定义采购领域契约与编排配置。

## 什么是 Domain Pack？

Domain Pack 是 **与代码分离的业务配置**，包含：

1. **品牌配置**: logo、颜色、字体等视觉元素
2. **UI 卡片**: 对话中使用的表单、列表、确认框等 UI 组件
3. **类目字段**: 不同采购类目的特定字段定义
4. **数据模式**: 字段总表契约、实体字段引用、阶段必填规则
5. **术语定义**: 专业术语、同义词、意图识别
6. **工作流节点**: 采购流程的各个步骤及其行为

## 目录结构

```
domain-pack/
├── branding/                          # 品牌配置
│   └── instance-branding.json         # xiaocai 品牌定义
│
├── cards/                             # UI 卡片模板
│   └── procurement-ui-cards.yaml      # 采购 UI 卡片
│
├── category-fields/                   # 类目字段
│   └── procurement-category-fields.yaml  # 采购类目字段
│
├── schema/                            # 数据模式
│   ├── procurement-field-dictionary.yaml # 字段总表（Sheet3 单一数据源）
│   └── procurement.yaml               # 实体结构 + 字段引用关系
│
├── terminology/                       # 术语定义
│   └── procurement.yaml               # 采购术语
│
├── workflows/                         # 工作流定义
│   └── procurement-workflow-nodes.yaml   # 采购工作流节点
│
├── contracts/                         # 领域执行契约
│   ├── procurement-search-sourcing-replace.yaml
│   ├── procurement-analysis-rfx-templates.yaml
│   ├── flare-contract-mapping.yaml
│   └── scenarios/
│       ├── server-procurement.yaml
│       ├── event-execution-procurement.yaml
│       ├── gift-customization-procurement.yaml
│       ├── content-production-procurement.yaml
│       └── travel-service-procurement.yaml
│
├── scripts/                           # 配置一致性校验
│   └── validate_domain_pack.rb        # Sheet1+Sheet3 静态校验脚本
│
└── README.md                          # 本文件
```

## 工作原理

### 1. FLARE 读取 Domain Pack

```
FLARE kernel
    ↓
读取 domain-pack/ 配置
    ↓
Decision Engine: 使用 terminology/ 进行意图识别
Knowledge Engine: 使用 schema/ 进行数据检索
Presentation Engine: 使用 cards/ 生成 UI
```

### 2. 前端使用 Domain Pack

```
xiaocai-frame-web
    ↓
读取 branding/ 配置品牌
    ↓
FLARE chat-ui 组件根据 cards/ 渲染 UI
```

## 配置说明

### branding/instance-branding.json

定义 xiaocai 的品牌元素：

- 名称: "小菜"
- Logo: light/dark 两种模式
- 颜色: 主色、次色、背景色等
- 字体: 字体家族和大小

### cards/procurement-ui-cards.yaml

定义采购流程中使用的 UI 卡片：

- `requirement-form`: 需求梳理表单
- `supplier-recommendation`: 供应商推荐列表
- `requirement-confirmation`: 需求确认卡片
- `knowledge-upload`: 文件上传卡片
- `procurement-progress`: 采购进度显示
- `intent-confirmation`: 意图确认卡片

每个卡片包含：
- 标题、描述
- 字段定义
- 操作按钮
- 数据绑定（使用 `{{ }}` 模板语法）

### category-fields/procurement-category-fields.yaml

定义 Sheet1 的三级目录与占位结构：

- 采购负责类 -> 一级品类 -> 二级品类
- 每个二级品类保留：
  - `各品类特殊需求字段占位: []`
  - `各品类特殊寻源要素占位: []`
- 首轮不填充 Sheet2 细节数据

### schema/procurement-field-dictionary.yaml

字段总表契约（Sheet3）：

- 中文字段键（首版主键）
- 字段业务口径与必填级别
- 类型/枚举/格式
- 示例值
- 阶段归属

### schema/procurement.yaml

定义采购相关的数据结构（引用字段总表）：

- `Project`: 采购项目
- `Requirement`: 采购需求
- `Analysis`: 需求分析输出
- `RFXStrategy`: RFX 策略输出
- `SourcingContext`: 后续寻源上下文（首轮引用保留）

每个实体包含：
- 字段引用（`field_refs`）
- 阶段必填集（`stage_field_sets`）
- 完整度规则（`completeness_rules`）

### terminology/procurement.yaml

定义采购领域的专业术语：

- `procurement_process`: 采购流程术语（需求梳理、供应商寻源等）
- `procurement_categories`: 采购类目术语
- `intents`: 意图及其触发词
- `supplier_attributes`: 供应商属性术语
- `quality_requirements`: 质量要求术语

用于：
- **意图识别**: Decision Engine 根据 triggers 识别用户意图
- **同义词处理**: 理解用户的不同表达方式
- **知识匹配**: Knowledge Engine 根据术语检索相关信息

### workflows/procurement-workflow-nodes.yaml

定义采购流程的首轮可执行闭环：

1. **requirement-collection**: 需求梳理
2. **requirement-analysis**: 需求分析
3. **rfx-strategy**: RFX策略

后续节点（supplier-search/quotation/negotiation/contract/delivery）仅占位，明确标注非首轮范围。

每个节点包含：
- 输入/输出
- 字段契约引用（`dictionary_ref`、`required_set_ref`）
- 完成条件与回退条件
- 输出契约

### contracts/

定义 procurement 领域可执行契约：

- `procurement-search-sourcing-replace.yaml`
- `procurement-analysis-rfx-templates.yaml`
- `scenarios/*.yaml`（5 个核心场景验收 fixture）
- `flare-contract-mapping.yaml`（联调映射）

## 业务对齐

Domain Pack 的配置与业务需求文档对齐：

| 业务文档 | Domain Pack 配置 |
|---------|-----------------|
| `docs/discussions/phase-1-procurement-product-logic.md` | `workflows/`, `cards/`, `terminology/` |
| `docs/discussions/phase-1-knowledge-base.md` | `schema/` (Knowledge, Project) |
| `docs/discussions/phase-1-member-management.md` | `schema/` (ownership) |

## 修改配置

修改 Domain Pack 配置后，需要：

1. **重启 FLARE kernel** - kernel 启动时加载配置
2. **重启前端** - 前端启动时加载品牌配置
3. **执行一致性校验**

```bash
cd deploy
make domain-pack-check
make domain-acceptance
```

## 扩展配置

添加新的采购类目：

1. 在 `category-fields/` 添加类目字段定义
2. 在 `terminology/` 添加类目术语
3. 在 `schema/` 增加对应字段引用关系（如需要）
4. 在 `cards/` 添加类目特定的 UI 卡片（如需要）

添加新的工作流节点：

1. 在 `workflows/` 添加节点定义
2. 定义节点的输入/输出、字段契约、完成条件与回退条件
3. 在 `cards/` 添加节点需要的 UI 卡片
4. 在 `terminology/` 添加节点相关的术语

## 注意事项

1. **YAML 语法**: 严格遵守 YAML 语法，注意缩进
2. **数据绑定**: 使用 `{{ }}` 进行数据绑定，确保字段名称正确
3. **版本控制**: Domain Pack 应该版本控制，方便回滚
4. **环境隔离**: 开发、测试、生产环境可以使用不同的 Domain Pack

## 参考文档

- 业务需求: `../docs/discussions/`
- 架构设计: `../docs/architecture/`
- FLARE 文档: `/Users/dantevonalcatraz/Development/F.L.A.R.E/`
