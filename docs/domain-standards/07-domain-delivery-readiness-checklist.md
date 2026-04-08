# 07 Domain Delivery Readiness Checklist

## 边界

- 本清单用于发布前领域交付门禁。
- 只有勾选项完成，才可宣称“domain ready”。

## 标准清单

### A. Taxonomy Readiness

- [ ] 核心采购类目（首批场景）已定义并可驱动字段加载
- [ ] taxonomy 扩展路径明确（配置优先）

### B. Field Model Readiness

- [ ] 字段总表为单一来源
- [ ] common/category-specific 分层完成
- [ ] 字段元数据完整可消费

### C. Workflow Readiness

- [ ] 首轮关键阶段可进入/退出/回退
- [ ] blocker 与 chooser 触发条件明确

### D. Search/Sourcing/Replace Readiness

- [ ] search 已绑定 target_field
- [ ] evidence 结构完整并可追溯
- [ ] replace 规则与 replace history 可执行
- [ ] sourcing 推荐理由结构化

### E. Analysis/Document Readiness

- [ ] analysis 依赖字段矩阵完整
- [ ] RFI/RFQ/RFP/RFB 模板依赖清晰
- [ ] 缺关键字段时不会伪造完整输出

### F. Scenario Acceptance Readiness

- [ ] 5 个核心场景至少主链路通过
- [ ] 场景测试包含预期分类/字段/输出断言

### G. Project Archiving Readiness

- [ ] 关键输出可归档到 Project
- [ ] 字段变更与输出版本可追溯

### H. Release Gate Readiness

- [ ] `make domain-acceptance` 通过（包含 domain-pack-check + api-smoke 断言）

## 验收

- 所有 must-have 勾选通过。
- 有未通过项时给出阻塞原因与修复责任人。

## 典型反例

- 仅凭 UI 可演示就宣布可交付。
- checklist 缺失 search/replace/sourcing 项。

## 不做什么

- 不跳过门禁直接进入对外发布。
