# 10 xiaocai instance 冻结方案与硬改计划（执行版）

## 0. 目标（本次冻结的唯一目标）

在不改动 `FLARE kernel/runtime` 职责前提下，完成 xiaocai instance 的**可复制、可交付、可扩展**架构冻结，满足“第二客户可快速复制上线”。

---

## 1. 冻结结论（立即生效）

### 1.1 xiaocai instance 必须承接产品编排（不是薄壳）

xiaocai 不是“只配配置”的薄 instance。  
xiaocai 必须保留并显式承接：

- requirement intake 闭环
- workbench 投影语义
- analysis / sourcing / artifact 应用链路编排
- procurement 领域语义与策略

### 1.2 同时必须禁止复制 FLARE 通用底座

xiaocai 不得复制：

- stream/session/transport 通用引擎
- kernel runtime 基础机制
- 可由 FLARE 通用库统一提供的协议解析逻辑

---

## 2. 目录与职责冻结（v1）

```text
procurement-agents/
├── domain-packs/        # 采购领域内容与规则（主资产）
├── tenant-config/       # 客户/租户覆盖（品牌、模式开关、策略差异）
├── adapters/
│   ├── kernel/          # kernel 服务壳与实例化（不改 kernel 内核）
│   └── http_api/        # transport 入口 + 应用层调用（禁止巨型编排）
├── frame/web/           # workbench 展示与交互（禁止发明后端真状态）
├── deploy/              # 部署脚手架与环境编排
└── docs/                # 架构/契约/执行基线文档
```

### 2.1 `pack-registry` 处理结论

- 已从 instance 主链路移除，并从仓库目录中删除。
- `domain-packs + tenant-config + bindings` 是当前默认交付收口。
- 若其能力属于平台通用资产，回收至 FLARE 平台仓处理。
- 若为历史迁移产物，仅保留文档记录，不再保留独立目录层。

---

## 3. 硬约束（Hard Rules）

### 3.1 Web 层

允许：
- 视图渲染、交互状态、工作台展示投影
- 对应用层 contract 的显示映射

禁止：
- 自定义 authoritative stream state machine
- 自定义协议语义（`done/error/cards` 终态规则不在 Web 层定义）
- UI fallback 替代后端 workflow 判定

### 3.2 HTTP API 层

允许：
- 输入校验、鉴权、调用应用层、响应输出
- 必要的 session/project 边界校验

禁止：
- 巨型 orchestrator 逻辑堆叠在 route/router
- 在 transport 层拼接大量业务语义与工作流状态机

### 3.3 Domain 层（xiaocai 核心）

必须承接：
- 字段体系、缺失字段规则、分析模板语义、寻源判定
- 状态推进 owner（intake/readiness/analysis/sourcing/artifact）

禁止：
- 直接依赖 provider SDK、HTTP framework、ORM transport 对象

### 3.4 FLARE 边界

必须：
- 通用协议与运行时机制优先使用 FLARE
- xiaocai 仅做产品级扩展和投影

禁止：
- 在 xiaocai 内复制 FLARE 内核能力

---

## 4. 现状问题归因（本次硬改触发原因）

当前链路暴露出三类问题：

1. **运行时依赖漂移**：仍存在 `docs/contracts/...` 这类 repo-relative 运行时依赖。
2. **层间职责重叠**：Web/API 同时对 stream/message 终态做决策，形成双重状态机。
3. **实例可复制性不足**：新增客户时需要手工调试大量非领域问题。

---

## 5. 大刀阔斧改造（硬处理）分阶段

## Phase 1（立即）：冻结与止血

目标：先稳定交付，不再继续增加架构债务。

动作：
- 冻结目录职责与边界（本文件生效）。
- 停止新增 Web/API 自定义协议分支逻辑。
- 统一把“运行时必需资源”迁到稳定可挂载路径（不再依赖 `docs/...`）。

产出：
- 冻结文档（本文件）
- 运行时依赖清单（必须可审计）

验收门：
- 新增代码不得引入 `docs/...` 运行时读取
- route 文件不新增业务编排分支

## Phase 2（硬改核心）：链路去重与 owner 收敛

目标：同一件事只有一个 owner。

动作：
- 收敛 stream/message 终态策略 owner（不再 Web+API 双决策）。
- API 仅做 transport + application call，复杂编排迁入 application/workflow。
- 抽离并显式化 intake/analysis/sourcing/artifact 状态推进 owner。

产出：
- owner map（状态归属矩阵）
- 精简后的 router/api 文件（薄入口）

验收门：
- route 层函数复杂度与分支数显著下降
- 状态推进点可追踪到单一 workflow owner

## Phase 3（模板化）：第二客户复制就绪

目标：形成“可复制实例模板”。

动作：
- 固化 tenant onboarding 模板（tenant-config + domain-pack 组合规范）。
- 固化 deploy 参数模板（端口、认证、依赖服务、健康检查）。
- 输出“新客户 1 天内起盘”操作手册。

产出：
- instance-template checklist
- tenant onboarding runbook

验收门：
- 新租户从模板到可用环境≤1天
- 无需改动核心链路代码即可切换客户

---

## 6. 回滚与风险控制

每个阶段必须具备：

- 清晰回滚点（tag/commit）
- 最小回滚路径（仅回滚该阶段改动）
- 受影响链路 smoke（auth/chat/stream/session/source）

---

## 7. 本周执行清单（强执行）

1. 输出并确认状态 owner map（必须）。
2. 锁定并迁移所有 runtime contract 读取路径（必须）。
3. 清点 `frame/web/src/**` 与 `adapters/http_api/**` 中重复协议逻辑并列出删除清单（必须）。
4. 移除 `pack-registry` 对主链路的依赖（必须）。
   - 当前解释：主链路已默认以 `domain-packs` 为主源，`pack-registry` 目录已删除。
5. 形成第二客户模板化交付脚手架（必须）。

---

## 8. 非目标（避免跑偏）

- 不在本阶段重写 FLARE kernel。
- 不在本阶段引入新的通用内核实现。
- 不做“边修边扩”式功能叠加。

---

## 9. 冻结生效说明

本文件为 xiaocai instance 当前执行基线。  
后续设计/开发/评审如与本冻结冲突，默认按本文件执行；若需例外，必须提交显式 ADR 并标注回滚策略。
