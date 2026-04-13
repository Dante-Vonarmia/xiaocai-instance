# xiaocai instance 技术范围与技术路线定稿（锁版）

## 1. 一句话定稿

小采 instance 是采购领域 canonical-state 驱动的任务系统，不是关键词路由聊天壳；核心抽象固定为 `CanonicalState + FieldPolicy + WorkItem + Artifact + ContractMapper`，扩展固定走规则/模板/知识/评分配置，不改 `service/router/UI` 主流程代码。

## 2. 技术范围冻结（本期）

### 2.1 本期必须覆盖

1. 需求梳理（字段推进、缺口识别、问题生成）
2. 需求分析（readiness 触发、分析输出）
3. 智能检索（证据回填）
4. 智能寻源（候选筛选与评分结果入状态）
5. RFX 策略与草稿输出（RFI/RFQ/RFP/RFB）
6. 文档输出与 Project 归档
7. 知识调用与沉淀复用

### 2.2 本期不覆盖

1. 新工作台系统
2. 自定义流程设计器
3. 脱离 canonical contract 的 UI 私有流程
4. 重写 FLARE 底座能力

## 3. 固定技术路线

1. 主状态：单一 `CanonicalState` authoritative truth
2. 编排：统一主流程 + WorkItem 子任务
3. 问题生成：`apply_answer -> select_next_field -> build_question`（policy 驱动）
4. 执行：analysis/retrieval/sourcing/document 均走 executor 契约回写
5. 产物：artifact schema 化（非自由文本）
6. 对外：contract mapper 对接现有 external contract，保持兼容

## 4. 明确禁止

1. 禁止关键词命中即切流程
2. 禁止 `service.py` 业务主脑化
3. 禁止 `router.py` 推断业务语义
4. 禁止 UI 补写 `current_question/missing_fields/flow_state`
5. 禁止各能力各自一套状态机
6. 禁止 artifact 仅文本回复无结构
7. 禁止 domain 逻辑散落 transport/frontend

## 5. 变更控制

1. 新增采购场景必须优先走 `domain-pack/policy/template/knowledge/scoring` 扩展。
2. 任何改动若要求修改 `service/router/UI` 主流程判断，默认判定为不合格方案。
3. 上述规则作为后续 Codex 实施评审门槛。
