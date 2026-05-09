# 第3章 外部数据与 MCP 接入手册

## 3.1 当前通道现状

| 通道 | 当前状态 | 入口 |
|---|---|---|
| xiaocai DB | 已有本库 healthcheck | `POST /settings/connectors/xiaocai_db/test` |
| external search | 已有 connector 概念，待真实调用 | `external_search_healthcheck_url` |
| MCP Gateway | 已有 connector 概念，待 JSON-RPC 实现 | `mcp_healthcheck_url` |
| source retrieval | 已有 route plan 与 simulated attempt results | `POST /retrieval/search` |

## 3.2 注册与测试 connector

1. 读取 registry：

```bash
GET /settings/connector-registry
```

2. 启用 connector：

```bash
PATCH /settings/connectors/{key}
```

3. 测试 connector：

```bash
POST /settings/connectors/{key}/test
```

4. 配置寻源优先级：

```bash
PUT /settings/search-sources
```

## 3.3 模拟外部数据库建议

下周只做只读模拟库，不做生产级同步。

建议至少准备两个 mock DB：

1. `mock_supplier_db`：供应商画像、主营品类、地区、资质、风险。
2. `mock_price_case_db`：历史报价、案例、交付周期、验收结果。

返回结果必须先 normalize 成 evidence/candidate contract，再进入寻源链路。

## 3.4 MCP 最小规范

MCP 当前对齐 2025-11-25 specification。  
MCP 使用 JSON-RPC 2.0；Streamable HTTP 应提供单一 MCP endpoint，并支持 POST/GET。当前优先支持最小服务端能力：

1. `initialize`
2. `tools/list`
3. `tools/call`
4. 可选：`resources/list`
5. 可选：`resources/read`

建议先暴露两个 mock tool：

1. `search_suppliers`
2. `lookup_price_cases`

参考：

- https://modelcontextprotocol.io/specification/2025-11-25/basic/index
- https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- https://modelcontextprotocol.io/specification/2025-11-25/server/resources

## 3.5 验收口径

一次端到端验收必须能看到：

1. connector 已启用且 healthcheck 通过。
2. search source policy 选择了正确的 default/fallback connector。
3. `POST /retrieval/search` 返回 route plan。
4. attempt results 能说明 primary/fallback 是否执行、成功或失败。
5. 命中结果能追溯到 source、connector、matched field。

## 3.6 LLM Provider 降级验收

LLM provider 降级由 FLARE provider router 负责，xiaocai 只消费配置和观测结果。

当前需要验证的配置项：

1. `MODEL_ROUTER_CANDIDATES_JSON`
2. `MODEL_PROVIDER_HEALTH_JSON`
3. `MODEL_PROVIDER_HEALTH_FILE`
4. `MODEL_PROVIDER_QUOTA_JSON`
5. `MODEL_ROUTER_FALLBACK_BY_INTENT_JSON`
6. `LLM_PROVIDER_TIMEOUT_BY_INTENT_JSON`

验收场景：

| 场景 | 输入 | 预期 |
|---|---|---|
| 主模型健康失败 | health 标记 primary disabled | 自动跳过 primary |
| 主模型额度耗尽 | quota 标记 primary exhausted/over_quota | 自动选择下一候选 |
| 主模型超时 | timeout-by-intent 设置低阈值 | 返回 fallback 模型结果 |
| 主模型 500 | mock provider 返回 500 | 返回 fallback 模型结果 |
| 全部失败 | 所有候选不可用 | 返回显式错误，不伪造业务结果 |

每次降级必须可在 `provider_trace` 或 routing decision 中看到 provider、model、status、reason。

## 3.7 不做什么

1. 不在本阶段做生产级 DB 同步。
2. 不把 MCP tool 原始返回直接作为 domain truth。
3. 不在 `chat/router.py` 中继续追加外部通道编排。
4. 不把外部数据源优先级写死在 FLARE Core。
5. 不在 xiaocai 侧重写 LLM provider router。
