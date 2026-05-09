# 11 xiaocai × FLARE DB / MCP Integration Plan

更新时间: 2026-05-08

## 1. 目标

下周目标不是继续改 FLARE Core，而是在 xiaocai instance 侧完成可演示、可验收的接入闭环：

1. domain pack 作为采购上下文来源稳定注入。
2. instance API 能管理和测试模拟外部数据库、外部搜索、MCP Gateway。
3. 检索/寻源链路能输出明确 route plan、attempt results、context refs。
4. LLM provider 降级链条可配置、可观测、可回归。
5. 手册能说明如何改 domain pack、如何接外部数据、如何验证通道。

## 2. 当前审计结论

### 2.1 已具备

- `domain-packs/**` 已有活动采购、礼品定制、shared rules、字段字典、品类目录、术语表。
- `scripts/validate_domain_packs.py` 与 `tests/domain_packs/**` 已覆盖静态校验。
- `adapters/http_api/src/xiaocai_instance_api/chat/orchestration/contract_loader.py` 已能解析 `domain-packs`。
- `connector_registry` / `search_source_policies` / `connector_status` 已在 storage migration 中建立。
- `GET /settings/connector-registry`、`PUT /settings/search-sources`、`POST /retrieval/search` 已存在。
- FLARE 已有 LLM provider router 基础：`MODEL_ROUTER_CANDIDATES_JSON`、`MODEL_PROVIDER_HEALTH_JSON/FILE`、`MODEL_PROVIDER_QUOTA_JSON`、`MODEL_ROUTER_FALLBACK_BY_INTENT_JSON`、`LLM_PROVIDER_TIMEOUT_BY_INTENT_JSON`、`provider_trace`。

### 2.2 仍需补齐

- MCP 当前只有 `mcp_gateway` healthcheck 概念，尚未实现 MCP JSON-RPC 规范交互。
- 外部数据库当前只有 `xiaocai_db` 本库健康检查，尚未支持模拟外部只读库。
- `retrieval/search` 当前仍是本地 source hits + simulated attempt results，不是真实多源调用。
- xiaocai deploy/env 尚未冻结 LLM provider 降级矩阵与验收脚本。
- `chat/router.py` 已超过 600 行，后续不能继续在 router 增加通道编排。

## 3. 下周排期

| 日期 | 任务 | 产出 | 验收 |
|---|---|---|---|
| 2026-05-11 | 冻结接入合同与 fixture 设计 | connector config 样例、模拟 DB 表结构、MCP tool/resource 清单、LLM fallback env 矩阵 | 文档能说明每个 connector 与 provider 的输入输出 |
| 2026-05-12 | domain pack context export + provider 配置落点 | 基于现有 `terminology`、`category-fields`、`schema` 输出 context payload；deploy/env 增加 LLM router 配置示例 | 不新增采购逻辑到 FLARE Core；不在 xiaocai 重写 provider router |
| 2026-05-13 | 模拟外部数据库接入 + provider health/quota 降级 | 至少 2 个只读 mock DB；health/quota fixture 覆盖主模型不可用/额度耗尽 | healthcheck + sample query 可通过；主 provider disabled/exhausted 时自动跳下一候选 |
| 2026-05-14 | 模拟 MCP Gateway 接入 + provider timeout/fallback | 最小 MCP endpoint；timeout-by-intent 与 fallback-by-intent 样例 | MCP 对齐 2025-11-25；primary timeout/500 时有 fallback result 与 provider_trace |
| 2026-05-15 | 端到端通道验收 | domain context + source policy + DB/MCP route plan + LLM provider_trace | smoke tests 与手册步骤全部通过 |

## 3.1 LLM Provider 降级链条排期

| 任务ID | 日期 | 任务 | Owner | 输出 | 验收 |
|---|---|---|---|---|---|
| LLM-FB-001 | 2026-05-11 | 审计并冻结 provider 降级输入合同 | FLARE + xiaocai | provider candidates、health、quota、fallback、timeout 配置矩阵 | 配置项可追溯到 FLARE contract/code；不新增 xiaocai 私有 router |
| LLM-FB-002 | 2026-05-12 | xiaocai env/deploy 消费配置 | xiaocai | `deploy/.env.example` / production env 示例方案 | instance 可通过环境变量切换候选模型、健康状态、额度状态 |
| LLM-FB-003 | 2026-05-13 | health/quota 降级回归 | FLARE + xiaocai | health/quota fixture 与 smoke 命令 | disabled/exhausted provider 被跳过，结果进入下一候选 |
| LLM-FB-004 | 2026-05-14 | timeout/error fallback 回归 | FLARE + xiaocai | timeout-by-intent、fallback-by-intent 验收用例 | primary timeout/HTTP 500 时返回 fallback，并记录 `provider_trace` |
| LLM-FB-005 | 2026-05-15 | 联合链路验收 | xiaocai | chat/run、chat/stream、retrieval 场景观测表 | 用户可用回复不中断；provider 降级原因可审计 |

## 4. 实施边界

### xiaocai 负责

- 采购字段、关键词、品类、模板、评分、推荐策略。
- connector registry 与 tenant/project 级别的启用、排序、策略覆盖。
- 模拟外部数据库与 MCP Gateway 的实例接入。
- 将外部返回 normalize 成 xiaocai retrieval/evidence contract。

### FLARE 负责

- 通用 intake/canvas/stream/kernel runtime。
- 通用 domain pack loader 能力、canonical projection、rule execution hook。
- 不承载采购词汇、品类、供应商评分、RFX 业务规则。

## 5. 最小验收命令

```bash
python3 scripts/validate_domain_packs.py
python3 -m unittest discover -s tests/domain_packs -p 'test_*.py' -v
./.venv/bin/python -m pytest adapters/http_api/tests/test_integrations.py adapters/http_api/tests/test_domains.py adapters/http_api/tests/test_sources.py -q
```

## 6. 风险与控制

1. 不把 MCP/DB 调用逻辑塞进 `chat/router.py`。
2. 不把 provider 原始 payload 直接作为 domain truth。
3. 不在 xiaocai 复制 FLARE stream/session runtime。
4. mock DB 与 mock MCP 必须走 connector/adapter 边界，便于后续替换真实服务。
5. 每个临时绕行必须更新 `docs/flare-dependency-gap-log.md`。
