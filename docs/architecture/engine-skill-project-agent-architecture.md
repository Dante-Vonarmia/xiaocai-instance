# Engine / Skill / Project Agent 架构说明

本文档保留为总述入口。

正式说明请按以下文档阅读：

1. [架构总览](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/01-architecture-overview.md)
2. [Kernel Runtime Engines](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/02-kernel-runtime-engines.md)
3. [Decision / Execution / Skills](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/03-decision-execution-and-skills.md)
4. [Project Agent 与 Subagent](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/04-project-agent-and-subagents.md)
5. [xiaocai 当前结构到目标架构映射](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/05-xiaocai-current-to-target-mapping.md)
6. [xiaocai 改造阶段说明](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/06-xiaocai-refactor-phases.md)

核心结论摘要：

1. `xiaocai` 属于 `Project Agent`
2. `Kernel` 是平台公共底座，由 7 个 `Engine` 组成
3. `Skill` 主要属于 `Decision Engine` 与 `Execution Engine` 这条动作链
4. `Context`、`Memory`、`Observation`、`Presentation`、`Ingestion` 更偏 `Kernel Runtime`
5. `Subagent` 属于项目内组合层，不是当前主要抽象和包化对象
