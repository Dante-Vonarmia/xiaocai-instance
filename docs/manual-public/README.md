# xiaocai 手册总述

> 版本 v0.1  
> 更新时间 2026-05-08

## 1. 产品定位

xiaocai 是运行在 FLARE 之上的采购场景 instance。  
它不重写 FLARE Core，而是把采购领域资产、外部数据源、工作台投影和用户可见闭环装配成可交付产品。

## 2. 当前手册范围

本手册先覆盖下周联调必须掌握的内容：

0. xiaocai × FLARE 当前能力清单、状态与缺口。
1. domain pack context 如何调整和验证。
2. 外部数据库如何模拟、注册、健康检查。
3. MCP Gateway 如何按规范接入最小工具/资源。
4. 检索/寻源 route plan 如何验收。

## 3. 与 FLARE 手册的关系

FLARE 手册说明通用产品与平台能力。  
xiaocai 手册只说明采购 instance 的使用、配置、接入与验收方式。

## 4. 当前版本说明

当前版本已具备：

1. domain-packs 资产与静态校验。
2. connector registry 与 integration status API。
3. source metadata 与 context priority 信号。
4. retrieval policy route plan 与 simulated attempt results。

当前版本待补齐：

1. 真实外部只读 DB adapter。
2. MCP JSON-RPC 最小交互。
3. 外部检索结果到 evidence contract 的 normalize。

## 5. 手册章节

1. [第0章 xiaocai × FLARE 能力清单](./00-capability-inventory.md)
2. [第2章 Domain Pack Context](./01-domain-pack-context.md)
3. [第3章 外部数据与 MCP 接入手册](./02-external-data-and-mcp-runbook.md)
