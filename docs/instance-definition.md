# xiaocai instance 定义（P0）

## 一句话定性
xiaocai instance 是基于 FLARE Core 的采购领域实例层，用领域资产把采购需求转成可执行、可产出、可解释的采购动作与产物。

## 目标用户
- 一线采购同学（需求梳理、寻源、比选）
- 业务需求方接口人（补齐需求、确认约束）
- 采购管理者（看风险、看推荐、看决策依据）

## 核心价值
- 把采购需求从“描述”收敛为“结构化字段 + 缺口 + 下一步动作”
- 把分析、寻源、评分、RFX建议沉淀为可复用资产
- 把输出交付成业务可直接使用的标准产物

## 责任边界

### xiaocai 负责
- procurement domain pack（字段、问询策略、分析模板、寻源规则、评分框架、RFX路由规则）
- procurement-specific 资产模板与业务产物定义
- 将 FLARE 的通用编排能力映射为采购场景可执行流程

### FLARE Core 负责
- kernel / orchestration / canonical contract / work item 调度
- 通用状态、执行框架、协议与运行时
- 不含采购行业特定语义

## 当前运行口径（domain-pack opt-in）

- FLARE 不默认启用 generic domain pack；未显式配置 `domain_pack_domain` 时，不展示任何 module capability。
- xiaocai 是显式 opt-in 业务实例；请求或会话必须显式指定 `domain_pack_domain=xiaocai` 才启用 xiaocai pack。
- xiaocai instance 转发给 FLARE 的请求必须携带：
  - `instance_id=xiaocai`
  - `domain_pack_domain=xiaocai`
  - `domain_pack_version=default`
- 当前 xiaocai pack 只启用 `requirement_intake` 与 `analysis_mode`。
- 当前不启用 `intelligent_sourcing`；这表示未配置/未启用寻源模块，不是前端隐藏寻源。
- UI 只能渲染 backend 返回的 canonical `module_prompt_registry` / capability projection，不得本地补默认 module 或从 generic 继承 module。

## 不负责范围
- 不重写 FLARE 的 mode/orchestration/kernel 主流程
- 不做“另一个通用聊天产品”
- 不做“另一个工作流引擎”
- 不以 UI 页面扩展作为一期起点
- 不承诺全品类全流程采购平台

## 第一阶段边界（P0）
- 场景：活动采购、礼品定制
- 目标：完成“需求梳理 -> 需求分析 -> 供应商筛选与评分 -> RFX动作建议 -> 标准产物输出”最小闭环；当前实际展示能力以 `module_prompt_registry` 中启用的 `requirement_intake`、`analysis_mode` 为准
- 交付形态：文档化 domain assets + 可被后续开发直接消费的规范

## 输入 / 输出 / 依赖 / 暂不做

### 输入
- 业务锚点材料（采购自动化体系、活动与礼品实践、供应商筛选维度、RFX选择逻辑）
- FLARE Core 既有边界与 canonical contract

### 输出
- 可执行的采购实例文档资产（本轮 10 份文档）
- 明确的 P0 场景与资产优先级

### 依赖
- FLARE Core 提供稳定通用运行能力
- xiaocai 维护 domain assets 并持续迭代

### 暂不做
- UI 信息架构重构
- 后端新能力编码
- 跨品类大规模扩展

## 上下文连续性边界（2026-05-19 补充）

### xiaocai adapter 负责
- 会话主键连续性（同一用户回合必须落在同一 `session_id`）。
- 短回复承接（如“crm”）的最小字段归一化与状态延续。
- 产品级分流语义（如“直接给方案”）与追问门控的优先级控制。
- 在不改写 FLARE kernel 的前提下，提供必要的结构化上下文信号（context/domain prior）。

### FLARE Core 负责
- kernel 内推理与通用编排执行。
- canonical contract 与通用运行时语义稳定。
- 不承接 xiaocai 采购场景的产品级问答策略细节。

### 判责原则
- 若消息存储在同一 `session_id` 且用户仍感知“失忆”，优先归因 xiaocai adapter 的状态承接/策略分流层。
- 若请求未到达或会话主键漂移，再回查 transport/session 接入层。

## 回复策略微调归属（2026-05-19 补充）

目标：在不操纵模型判断结果的前提下，提升用户对“当前进度与全貌”的可见性。

### 归属层
- xiaocai orchestration / projection 层负责“如何展示进度与全貌”。
- FLARE Core 仍负责通用 kernel/orchestration/runtime，不承接小彩产品语义。

### 产品策略原则
- 回答通道：保持模型与策略计算原结果，不人为改写结论。
- 导航通道：并行展示阶段目录、当前位置、已确认/待确认、下一步动作。
- 若信息不完整，可展示 `v0` 草案与待确认清单，不等于强行给最终结论。
