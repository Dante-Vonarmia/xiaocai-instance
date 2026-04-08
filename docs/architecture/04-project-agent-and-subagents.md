# Project Agent 与 Subagent（正式定位）

## 1. 文档目的

定义项目装配层的正式边界，避免项目能力与平台能力混写。

---

## 2. Project Agent 正式定位

`xiaocai` 是 Project Agent。

Project Agent 负责：

1. 装配业务闭环流程。
2. 装配项目策略、规则和配置。
3. 对外输出可用业务能力。

Project Agent 不等于某一个 Engine。

---

## 3. Subagent 正式定位

Subagent 是项目内部的职责组织单元，用于承接分角色执行。

Subagent 负责：

1. 组合多个动作能力。
2. 在项目语境下执行局部任务。

Subagent 不作为当前主要产品化抽象对象。

---

## 4. 与业务闭环的对应

1. Project Agent 负责端到端闭环完整性。
2. Subagent 负责闭环中的角色化分工执行。
3. Kernel 负责公共支撑，不替代项目装配。

---

## 5. 与平台边界关系

FLARE 与 instance 边界约束由 `07-flare-instance-boundary.md` 独立管理。
