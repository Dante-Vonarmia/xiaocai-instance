# xiaocai Docs System

最后更新: 2026-05-08

## 1. 文档体系定位

`docs/` 是 xiaocai 的正式知识库，不再按临时 MVP 文档堆叠方式维护。  
所有新增文档必须先归类，再落文件；禁止继续在 `docs/` 根目录追加临时专题文档。

## 2. 正式阅读顺序

1. [Domain Standards](./domain-standards/README.md)  
   采购领域规则、字段、流程与验收口径。
2. [Architecture](./architecture/README.md)  
   xiaocai 与 FLARE 边界、分层、集成与执行计划。
3. [Contracts](./contracts/xiaocai-instance-canonical-contract-v1.md)  
   对外/对内稳定数据契约、schema、registry。
4. [Planning](./planning/README.md)  
   当前任务排期、里程碑、验收门禁。
5. [Manual Public](./manual-public/README.md)  
   面向使用、接入、运维和联调的手册。
6. [ADR](./adr/)  
   已接受的架构决策记录。

## 3. 目录职责

| 目录 | 职责 | 是否权威 | 新增规则 |
|---|---|---|---|
| `domain-standards/` | 采购领域标准、字段、流程、验收 | 是 | 领域规则必须落这里 |
| `architecture/` | 系统边界、分层、集成计划、治理方案 | 是 | 架构与排期计划落这里 |
| `contracts/` | schema、canonical contract、registry | 是 | 合同字段变更必须落这里 |
| `planning/` | 任务排期、里程碑、周计划、验收门禁 | 是 | 所有当前排期必须落这里 |
| `manual-public/` | 使用手册、接入手册、运维 runbook | 是 | 面向执行者的操作说明落这里 |
| `adr/` | 不可轻易反复修改的决策记录 | 是 | 决策冻结后再进入 |
| `migrations/` | 迁移说明与兼容路径 | 是 | 只放迁移专项 |
| `benchmark/` | 性能、技术选型、实验依据 | 参考 | 不直接驱动产品合同 |
| `discussions/` | 历史输入、讨论、原始表格 | 否 | 仅背景追溯 |
| `docs/` 根目录 | 总入口与待迁移历史文件 | 过渡 | 不再新增专题文件 |

## 4. 当前待治理问题

1. 根目录仍有历史专题文档，需要分批迁入正式目录。
2. `discussions/` 中有历史业务输入，但不能继续作为实现验收来源。
3. `benchmark/` 内容较多，需保持为研究证据，不直接替代 contract。
4. 现有 README 曾引用 `archive/`，但当前目录未建立；归档策略需单独落地。

## 5. 新文档准入规则

新增文档前先判断类型：

1. 字段/品类/流程/验收标准 -> `domain-standards/`
2. 架构边界/集成计划/工程治理 -> `architecture/`
3. 数据结构/API/事件/schema -> `contracts/`
4. 任务排期/里程碑/周计划/验收门禁 -> `planning/`
5. 操作步骤/联调手册/部署手册 -> `manual-public/`
6. 冻结决策与取舍 -> `adr/`
7. 历史材料 -> `discussions/` 或后续 `archive/`

## 6. 治理方案

详细规则见：

- [12-documentation-system-governance.md](./architecture/12-documentation-system-governance.md)
