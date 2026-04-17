# xiaocai Domain Assets Map（P0 优先）

## 资产地图总览

| 资产类 | 作用 | 输入 | 输出 | 是否P0 | 上游依赖 | 主要消费者 |
|---|---|---|---|---|---|---|
| fields schema | 定义场景字段与填报口径 | 场景目标、业务约束 | 必填/推荐/可选字段清单 | 是 | 场景定义、业务锚点 | kernel, ui, operator |
| question flow / clarification policy | 缺失字段补问与追问顺序 | 已填字段、缺失字段、readiness规则 | 当前问题、下一步问题、补问策略 | 是 | fields schema, readiness标准 | kernel, ui |
| analysis template | 规范分析输出结构 | 结构化需求字段 | 场景分析文档骨架 | 是 | fields schema, 场景规则 | operator, business |
| sourcing rules | 定义寻源过滤与推荐规则 | 场景约束、供应商画像、预算/交期 | longlist 与过滤说明 | 是 | fields schema, 评分框架 | sourcing flow, operator |
| supplier scorecard | 统一供应商打分与解释 | 供应商信息、评估维度 | 评分表、排名、解释项 | 是 | sourcing rules, 评估维度定义 | operator, sourcing flow |
| rfx routing rules | 决定 RFI/RFP/RFQ/RFB | 项目类型、目标、预算、约束 | RFX建议 + 理由 + 缺口 | 是 | requirement结构、风险约束 | kernel, operator |
| artifact templates | 标准化产物交付格式 | 各阶段结构化结果 | 需求单/分析/评分/RFX等产物模板 | 是 | analysis/sourcing/rfx 结果 | operator, business |
| process guide | 业务执行快速指引 | 场景流程、角色分工 | 场景流程指引（分场景） | 否（P1） | 已稳定的P0流程 | operator |
| supplier handbook / management mechanism | 供应商管理规则与机制 | 供应商分层、准入/考核要求 | 手册、管理机制说明 | 否（P1） | 供应商治理策略 | operator, management |

## 资产依赖关系（简版）
1. fields schema -> question flow -> analysis/sourcing/rfx
2. sourcing rules + supplier scorecard -> shortlist 推荐
3. analysis/rfx/sourcing 结果 -> artifact templates
4. process guide / supplier handbook 依赖 P0 稳定结果再固化

## P0 最小资产包
- fields schema（活动、礼品）
- question flow / clarification policy（活动、礼品）
- analysis template（七段式 + 礼品结构）
- sourcing rules + supplier scorecard（活动、礼品）
- rfx routing rules
- artifact templates（P0产物）

## 输入 / 输出 / 依赖 / 暂不做

### 输入
- 业务锚点与场景优先级

### 输出
- 领域资产全景图与 P0 优先落地清单

### 依赖
- instance-definition 与 domain-scope 定位清晰

### 暂不做
- 未有锚点支撑的高级自动决策资产
