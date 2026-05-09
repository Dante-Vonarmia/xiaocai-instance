# 12 Documentation System Governance

更新时间: 2026-05-08

## 1. 目标

把 xiaocai 文档从 MVP 阶段的“专题堆叠”升级为长期可维护的文档体系。

目标状态：

1. 每类文档有唯一归属目录。
2. 权威文档与历史讨论分离。
3. 标准、合同、架构、手册、ADR 各自承担单一职责。
4. 新增开发任务能从标准或合同追溯到实现。
5. 手册面向执行，不混入未冻结设计推导。

## 2. 文档分层

| 层级 | 目录 | 内容 | 禁止 |
|---|---|---|---|
| L1 标准层 | `domain-standards/` | 领域边界、字段模型、流程规则、验收基线 | 写临时会议记录 |
| L2 架构层 | `architecture/` | 系统边界、分层、集成计划、治理方案 | 写业务字段细节 |
| L3 合同层 | `contracts/` | schema、canonical contract、registry | 写散文式说明 |
| L4 排期层 | `planning/` | 任务排期、里程碑、周计划、验收门禁 | 写架构论证或业务规则 |
| L5 决策层 | `adr/` | 已接受决策、取舍、回滚原则 | 写执行流水账 |
| L6 手册层 | `manual-public/` | 操作、联调、接入、运维说明 | 写未确认方案 |
| L7 证据层 | `benchmark/` | 选型、性能、实验、研究证据 | 直接替代合同 |
| L8 历史层 | `discussions/` | 原始输入、讨论、表格、背景材料 | 作为验收来源 |

## 3. 根目录治理

`docs/` 根目录只允许保留：

1. `README.md`
2. 历史待迁移文件

从 2026-05-08 起，不再新增根目录专题文档。  
已有根目录文件分批迁移或吸收到正式目录，迁移前不得继续扩写。

## 4. 历史根目录文件分类建议

| 当前文件 | 建议归属 | 处理方式 |
|---|---|---|
| `activity-procurement-pack.md` | `domain-standards/` 或 `manual-public/` | 已资产化内容只保留引用 |
| `gift-customization-pack.md` | `domain-standards/` 或 `manual-public/` | 已资产化内容只保留引用 |
| `supplier-evaluation-framework.md` | `domain-standards/` | 吸收到 sourcing/scorecard 标准 |
| `rfx-routing-spec.md` | `domain-standards/` / `contracts/` | 规则归标准，schema 归合同 |
| `artifact-output-spec.md` | `contracts/` / `manual-public/` | 输出结构归合同，操作归手册 |
| `domain-assets-map.md` | `architecture/` | 转为资产映射说明 |
| `domain-scope.md` | `domain-standards/` | 吸收到领域边界 |
| `gap-analysis.md` | `architecture/` | 吸收到治理/差距计划 |
| `next-step-plan.md` | `architecture/` | 被正式排期文档替代 |
| `flare-dependency-gap-log.md` | `architecture/` | 保留为 FLARE 缺口台账 |
| `flare-handoff-tasks.md` | `architecture/` | 保留为 FLARE 移交台账 |
| `permission-execution-checklist.md` | `manual-public/` | 转为运维/权限手册 |
| `instance-definition.md` | `architecture/` | 吸收到 instance 边界文档 |

## 5. 新文档模板要求

每篇正式文档必须包含：

1. 标题。
2. 更新时间。
3. Scope / 目标。
4. Owner 或职责边界。
5. 输入与输出。
6. 验收或使用规则。
7. 不做什么。

例外：

1. schema/json/yaml 合同文件按合同格式维护。
2. README 只作为目录入口，不承载详细设计。

## 6. 权威优先级

当文档冲突时，按以下顺序处理：

1. `contracts/`
2. `domain-standards/`
3. `architecture/`
4. `planning/`
5. `adr/`
6. `manual-public/`
7. `benchmark/`
8. `discussions/`

说明：

- ADR 记录决策原因，但具体字段与合同以 `contracts/` 为准。
- 手册只教怎么用，不决定系统真状态。
- discussions 只能作为背景，不直接驱动实现。

## 7. 分阶段治理计划

### Phase 1：入口冻结

目标：建立当前文档体系入口，不搬文件。

产出：

1. 更新 `docs/README.md`。
2. 更新各主目录 README。
3. 新增本文档。

验收：

1. 新文档有明确归属。
2. 根目录不再新增专题文档。

### Phase 2：根目录历史文件吸收

目标：逐个处理根目录历史文档。

规则：

1. 已资产化内容只保留引用，不复制长文。
2. 仍有效的规则迁入 `domain-standards/` 或 `contracts/`。
3. 仅背景材料迁入后续 `archive/` 或保持 read-only。

### Phase 3：合同与手册补齐

目标：让开发、联调、运维都有固定入口。

产出：

1. `contracts/README.md`
2. `adr/README.md`
3. `planning/README.md`
4. `manual-public` 分章节扩展。

### Phase 4：文档门禁

目标：文档进入开发验收流程。

门禁：

1. 业务规则改动必须指向 `domain-standards/`。
2. payload/schema 改动必须指向 `contracts/`。
3. 当前任务排期必须指向 `planning/`。
4. 架构例外必须指向 `adr/` 或 `architecture/`。
5. runbook 更新必须进入 `manual-public/`。

## 8. 不做什么

1. 不一次性移动全部历史文件。
2. 不重写历史讨论内容。
3. 不把 benchmark 结论直接升级为合同。
4. 不让手册替代 architecture / contracts。
5. 不在文档治理中顺手改代码。
