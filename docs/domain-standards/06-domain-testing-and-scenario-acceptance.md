# 06 Domain Testing And Scenario Acceptance

## 边界

- 本文定义领域验收，不替代平台连通性测试。
- `api-smoke` 只证明通路，不证明 procurement 能力闭环。

## 标准

### 测试类型

1. taxonomy classification fixtures
2. field extraction golden cases
3. workflow transition cases
4. chooser/blocker trigger cases
5. search mapping cases
6. sourcing recommendation cases
7. replace rule cases
8. template dependency cases
9. e2e scenario smoke tests

### 首批核心场景

1. 服务器采购
2. 活动执行采购
3. 礼品/定制采购
4. 内容制作/拍摄采购
5. 差旅服务采购

### 场景用例模板

- 输入示例
- 预期分类
- 预期字段提取
- 预期 blocker/chooser 行为
- 预期 search target
- 预期输出形态（analysis/RFX）

## 验收

- 每个核心场景至少有 1 条主链路通过样例。
- 每条样例可追溯到字段、阶段、证据、输出。
- blocker 行为可预测，不随机弹窗。

## 典型反例

- 只有聊天示例，没有结构化预期断言。
- 场景通过依赖人工主观判断。
- search/sourcing/replace 无独立测试。

## 不做什么

- 不把“模型看起来回答不错”当验收标准。
