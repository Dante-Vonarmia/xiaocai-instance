# xiaocai instance 边界与目录冻结（锁版）

## 1. 分层边界冻结

| 层 | 负责什么 | 不负责什么 |
|---|---|---|
| transport/router | auth/session/sse/contract 出口 | 业务决策、字段选择、问题生成 |
| orchestration service | 调用 state/policy/workitems，组织响应 | intent 关键词主路由 |
| canonical state | authoritative 状态保存与变更 | UI 展示推断 |
| policy/field graph | 字段规则、依赖、问法、readiness | transport 逻辑 |
| workitem planner | 任务创建/调度/完成判断 | UI/路由处理 |
| executors | 执行 intake/analysis/retrieval/sourcing/document | 持有主状态真源 |
| artifact builders | 结构化产物构建 | 主流程推进 |
| repositories | project/knowledge 持久化 | 业务编排 |
| UI projection | 渲染与提交答案 | 主状态推断 |

## 2. 目录冻结（后端）

```
adapters/http_api/src/xiaocai_instance_api/
  chat/
    orchestration/
      service.py
      contract_loader.py
      contract_mapper.py
      flows.py                # legacy fallback（兼容层，后续删除）
  domain/
    state/
    policy/
    workitems/
    executors/
    artifacts/
  repositories/
    project/
    knowledge/
```

## 3. 目录冻结（文档）

```
docs/
  architecture/
    08-xiaocai-instance-technical-scope-and-route-freeze.md
    09-xiaocai-instance-boundary-and-directory-freeze.md
  contracts/
    xiaocai-instance-canonical-contract-v1.md
```

## 4. 兼容层冻结

1. `chat/orchestration/flows.py` 仅作为过渡 fallback，不新增业务能力。
2. `router` 中 pending_contract 推断逻辑仅允许保留兼容映射，不允许继续扩展业务语义。
3. 前端兜底逻辑仅保留渲染容错，不得参与业务判断。
