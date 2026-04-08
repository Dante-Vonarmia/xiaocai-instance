# 03 Domain Workflows And Stage Rules

## 边界

- 本文定义 procurement 主链路阶段规则。
- 现有首轮可执行闭环: `requirement-collection -> requirement-analysis -> rfx-strategy`。
- search/sourcing/compare/replace 作为后续阶段必须先定义契约，不先散落实现。

## 标准

### 主流程

用户输入
-> 意图识别
-> 品类识别
-> 加载 common + category fields
-> requirement intake
-> clarify（按缺失字段）
-> requirement analysis
-> search
-> sourcing
-> compare
-> replace
-> rfx generation

### 硬规则

1. 先梳理，后检索。
2. 无初步结构化需求，不做大范围对比。
3. chooser 仅处理 blocker，不提前弹出。
4. search 必须带 `target_field` 或明确任务目标。
5. analysis 必须基于已确认字段。
6. 任一步失败可回退上一阶段。

### 阶段定义模板（每阶段必须具备）

- 输入
- 输出
- 进入条件
- 阻塞条件
- 回退条件
- 对 workspace 的影响

## 验收

- 三段首轮节点均有输入/输出/完成条件/回退条件。
- 流程可以解释“为什么停在当前阶段”。
- 阻塞场景不会直接跳过关键字段收集。

## 典型反例

- 未完成梳理即直接做供应商比较。
- chooser 在非 blocker 场景频繁触发。
- 分析结论不依赖字段，纯模型自由发挥。

## 不做什么

- 不在 domain 层重造平台状态机。
- 不把阶段跳转写成散落提示词。
