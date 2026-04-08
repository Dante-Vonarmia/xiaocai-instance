# 01 Domain Scope And Boundaries

## 边界

- `xiaocai` 定义: 运行在 FLARE 之上的 procurement domain instance。
- `xiaocai` 不定义平台 runtime，不重写 kernel，不重写通用协议。
- 采购语义必须收敛到 `domain-pack`，而不是散落在 UI、service、controller。

## 标准

1. 领域核心必须配置化表达:
- taxonomy
- field model
- category-specific fields
- workflows
- search mapping
- replace rules
- analysis/RFX templates
- scenario acceptance

2. 实例外壳定义:
- branding
- starter prompts/cards
- UI 壳样式

3. 平台复用硬约束:
- 复用 FLARE 的 workspace/contracts/storage/orchestration
- procurement-specific if/else 不得成为主要实现路径

## 验收

- 能明确区分“领域核心配置”与“实例外壳配置”。
- 任一采购规则可追溯到 `domain-pack` 文档或配置条目。
- 不存在为采购场景重造通用 session/workspace/event/storage 机制的代码改造需求。

## 典型反例

- 通过 UI 组件内部硬编码分支做品类判断。
- 通过 chat prompt 大段文字替代结构化字段规则。
- 在 instance API handler 写大量采购业务路由逻辑。

## 不做什么

- 不在 `xiaocai` 实现平台级状态机。
- 不在 `xiaocai` 重写 SSE/API 协议。
- 不把 branding 当主要交付成果。
