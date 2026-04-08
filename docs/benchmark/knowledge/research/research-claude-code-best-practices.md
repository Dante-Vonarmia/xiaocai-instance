# Claude Code 社区最佳实践调研报告

**调研日期**: 2026-03-08
**目标场景**: Scrum MCP Server + Hooks 工作流自动化系统
**调研来源**: awesome-claude-code, claude-code-showcase, claude-code-agents, claude-code-infrastructure-showcase

---

## 执行摘要 (Executive Summary)

本报告调研了 Claude Code 社区的最佳实践，重点关注：
1. Hooks 自动化模式（3种类型：Command/Prompt/Agent）
2. MCP Server 工具集成模式
3. 进度追踪与 Dashboard 实现
4. Agent 编排与协作模式
5. GitHub Actions 集成

**关键发现**:
- **Skill Auto-Activation** 是社区解决的最大痛点（diet103/infrastructure-showcase 9189★）
- **Stop Hook + Prompt Hook** 验收模式是质量保证核心
- **EXECUTION_LOG.md** 表格格式是进度追踪最佳实践
- **MCP Tool Naming** 遵循 `mcp__<server>__<tool>` 约定
- **GitHub Actions** 与 Claude Code 集成已成熟（官方 claude-code-action）

---

## 1. Features 清单（按优先级排序）

### P0 - 立即实现（核心价值）

#### Feature 1: Agent Execution Log（进度追踪表格）

**功能描述**:
记录每个 Agent 的执行状态、耗时、结果到 markdown 文件，实现实时进度看板。用户可以随时查看哪些 Agent 在跑、成功还是失败。

**参考项目**:
- [claude-code-agents](https://github.com/undeadlist/claude-code-agents) - `.claude/audits/EXECUTION_LOG.md`
- 格式示例：

```markdown
| Timestamp | Agent | Status | Duration | Findings | Errors |
|-----------|-------|--------|----------|----------|--------|
| 2026-03-08T10:30:00Z | scrum-master | COMPLETE | 12s | 3 | [] |
| 2026-03-08T10:32:15Z | issue-validator | ERROR | 5s | 0 | [missing parent] |
```

**实现复杂度**: 简单
- MCP 工具在 Agent 执行前后记录活动
- 追加到 markdown 表格（TSV格式）
- 更新统计数据（总运行次数、成功率、平均耗时）

**适用性**: 非常适合
- 用户需要"随时聚焦进度"，这个功能完美契合
- 表格格式易读，Markdown 原生支持
- 可扩展：添加 `Issue ID`、`Result Summary` 列

**建议优先级**: P0（立即实现）

**实现建议**:
```yaml
# .scrum/progress/execution-log.md 格式
| Timestamp | Tool | Issue | Status | Duration | Result |
|-----------|------|-------|--------|----------|--------|
| ISO-8601 | tool_name | ISSUE-ID | OK/FAIL | Xs | summary |

# MCP 工具自动追加
mcp__scrum__log_execution({
  tool: "create_issue",
  issue_id: "APP-054",
  status: "success",
  duration: 2.3,
  result: "Issue created successfully"
})
```

---

#### Feature 2: Stop Hook 验收模式（质量保证）

**功能描述**:
在 Claude 完成任务后，自动运行验收测试（shell 脚本或 Prompt Hook），阻止不合规的输出。

**参考项目**:
- [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) - 3238★
- [ChrisWiles/claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) - 5455★

**核心模式**:
```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": ".claude/hooks/validate-issue.sh",
        "timeout": 10
      },
      {
        "type": "prompt",
        "prompt": "检查生成的 Issue 是否符合 CLAUDE.md 第10.1节的格式要求",
        "model": "haiku"
      }
    ]
  }
}
```

**三种 Hook 类型**:
1. **Command Hook** - 执行 shell 脚本（确定性验证）
   - 示例：检查文件是否在 Repo 边界内
   - 返回 `exit 2` 阻止 Claude 停止（强制继续修复）

2. **Prompt Hook** - 使用 LLM 判断（语义验证）
   - 示例：检查 AC 是否符合 SMART 原则
   - 返回 `{"ok": false, "reason": "..."}` 阻止

3. **Agent Hook** - 启动子 Agent 验证（复杂验证）
   - 示例：读取多个文件，检查跨文件一致性

**实现复杂度**: 中等
- 需要设计验收规则（YAML 配置）
- Command Hook 简单（shell 脚本）
- Prompt Hook 需要编写验收 Prompt

**适用性**: 非常适合
- 用户需要"强制执行 CLAUDE.md 约束"
- 防止 AI 创建不合规的 Issue
- 防止跨 Repo 边界违规

**建议优先级**: P0（立即实现）

**实现建议**:
```bash
# .claude/hooks/validate-issue.sh
#!/bin/bash
# 检查 Issue 文件是否在正确位置

ISSUE_FILE="$CLAUDE_TOOL_OUTPUT_FILE_PATH"

# 检查1：文件在 .scrum/issues/ 目录
if [[ ! "$ISSUE_FILE" =~ ^\.scrum/issues/ ]]; then
  echo '{"block": true, "message": "Issue 必须创建在 .scrum/issues/ 目录"}' >&2
  exit 2
fi

# 检查2：文件名符合格式 REPO-NNN-description.md
if [[ ! "$ISSUE_FILE" =~ (APP|API|ENGINE|PLATFORM)-[0-9]{3,}-.+\.md$ ]]; then
  echo '{"block": true, "message": "Issue 文件名必须符合格式：REPO-NNN-description.md"}' >&2
  exit 2
fi

# 检查3：YAML Front Matter 存在
if ! grep -q "^---$" "$ISSUE_FILE"; then
  echo '{"block": true, "message": "Issue 缺少 YAML Front Matter"}' >&2
  exit 2
fi

# 通过验收
echo '{"feedback": "Issue 格式验证通过"}'
exit 0
```

**常见错误（必须避免）**:
- Stop Hook 无限循环：检查 `stop_hook_active` 变量
- 阻塞太久：合理设置 `timeout`（5-10秒）
- 过度验证：优先用 Command Hook，必要时才用 Prompt Hook

---

#### Feature 3: Skill Auto-Activation（智能技能激活）

**功能描述**:
根据用户 Prompt、文件路径、意图模式，自动建议激活相关 Skill，无需用户手动触发。

**参考项目**:
- [diet103/claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase) - 9189★
- **这是社区最受欢迎的功能**

**核心机制**:
1. **UserPromptSubmit Hook** 拦截用户输入
2. **skill-eval.js** 引擎分析 Prompt：
   - 提取关键词（keywords）
   - 匹配文件路径（pathPatterns）
   - 检测意图模式（intentPatterns）
   - 目录映射（directoryMappings）
3. **输出建议**：
   ```
   💡 建议激活 Skills:
   - scrum-workflow (score: 8) - 检测到关键词 'issue', 'sprint'
   - repo-boundary-check (score: 6) - 路径涉及多个 Repo
   ```

**配置示例** (`skill-rules.json`):
```json
{
  "skills": {
    "scrum-workflow": {
      "triggers": {
        "keywords": ["issue", "sprint", "epic", "story"],
        "keywordPatterns": ["\\bissue\\b", "create.*task"],
        "pathPatterns": [".scrum/issues/**"],
        "intentPatterns": [
          "(?:create|add).*(?:issue|task)",
          "(?:plan|organize).*(?:sprint)"
        ],
        "directoryMappings": {
          ".scrum/issues": "scrum-workflow"
        }
      },
      "priority": 9
    },
    "repo-boundary-check": {
      "triggers": {
        "keywords": ["xiaocai-app", "xiaocai-api", "cross-repo"],
        "intentPatterns": ["(?:modify|update).*(?:multiple repos|app.*api)"]
      },
      "priority": 8
    }
  }
}
```

**实现复杂度**: 中等
- 需要编写 skill-eval 引擎（Node.js 或 Python）
- 需要维护 skill-rules.json 配置
- 评分算法需要调优

**适用性**: 非常适合
- 用户有多个 Skill（scrum-workflow, repo-boundary, tdd, code-review）
- 新手容易忘记激活 Skill
- 提高 AI 工作效率

**建议优先级**: P0（立即实现）

**实现建议**:
```javascript
// .claude/hooks/skill-eval.js（简化版）
const rules = require('./skill-rules.json');

function evaluateSkills(prompt) {
  const matches = [];

  for (const [name, skill] of Object.entries(rules.skills)) {
    let score = 0;
    const reasons = [];

    // 检查关键词
    for (const keyword of skill.triggers.keywords || []) {
      if (prompt.toLowerCase().includes(keyword)) {
        score += 2;
        reasons.push(`关键词: ${keyword}`);
      }
    }

    // 检查意图模式
    for (const pattern of skill.triggers.intentPatterns || []) {
      if (new RegExp(pattern, 'i').test(prompt)) {
        score += 4;
        reasons.push(`意图匹配: ${pattern}`);
      }
    }

    if (score >= 3) {
      matches.push({ name, score, reasons, priority: skill.priority });
    }
  }

  // 按 priority 和 score 排序
  matches.sort((a, b) => b.priority - a.priority || b.score - a.score);

  return matches;
}

// 输出建议（不阻塞）
const matches = evaluateSkills(process.stdin);
if (matches.length > 0) {
  console.log('💡 建议激活 Skills:');
  matches.slice(0, 3).forEach(m => {
    console.log(`- ${m.name} (score: ${m.score}) - ${m.reasons.join(', ')}`);
  });
}
process.exit(0); // 不阻塞
```

---

### P1 - 高优先级（显著提升）

#### Feature 4: MCP Tool Progress Tracking（工具执行追踪）

**功能描述**:
记录每个 MCP 工具的调用情况（调用次数、成功率、耗时），生成统计报告。

**参考项目**:
- [ChrisWiles/claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) - `PostToolUse` Hook

**实现方式**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__scrum__*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/track-tool-usage.sh",
            "timeout": 2
          }
        ]
      }
    ]
  }
}
```

**追踪文件格式** (`.scrum/stats/tool-usage.json`):
```json
{
  "mcp__scrum__create_issue": {
    "total_calls": 123,
    "success": 118,
    "failure": 5,
    "avg_duration_ms": 234,
    "last_call": "2026-03-08T10:30:00Z"
  },
  "mcp__scrum__update_issue_status": {
    "total_calls": 89,
    "success": 89,
    "failure": 0,
    "avg_duration_ms": 156
  }
}
```

**实现复杂度**: 简单
- PostToolUse Hook 提供工具名称和结果
- 简单的 JSON 文件读写
- 可选：生成 Markdown 报告

**适用性**: 适合
- 了解哪些 MCP 工具最常用
- 发现失败率高的工具
- 优化性能瓶颈

**建议优先级**: P1（高优先级）

---

#### Feature 5: Agent Orchestration（Agent 编排协作）

**功能描述**:
实现 Orchestrator Agent 协调多个专业 Agent 协同工作，自动分配任务和汇总结果。

**参考项目**:
- [wshobson/agents](https://github.com/wshobson/agents) - 多 Agent 协作框架
- [Claude 官方文档](https://code.claude.com/docs/en/agent-teams) - Agent Teams

**核心模式**:
```markdown
# orchestrator.md

你是 Orchestrator Agent，负责协调其他专业 Agent。

## Available Agents:
- scrum-master: 创建和管理 Issue
- tech-intelligence: 调研技术方案
- cto-agent: 架构设计
- tdd-agent: 设计测试方案

## Workflow:
1. 分析用户需求
2. 确定需要哪些 Agent
3. 并行调用多个 Agent（使用 Task tool）
4. 汇总结果并返回

## Example:
用户: "实现字段提取功能"
→ 调用: tech-intelligence（调研轮子）
→ 调用: cto-agent（设计架构）
→ 调用: tdd-agent（设计 AC）
→ 调用: scrum-master（创建 Issue）
```

**实现复杂度**: 中等
- 需要定义 Agent 接口规范
- 需要任务分配逻辑
- 使用 Task tool 调用子 Agent

**适用性**: 非常适合
- 用户已有 4 个专业 Agent
- 需要自动化工作流
- 减少用户手动协调

**建议优先级**: P1（高优先级）

**实现建议**:
```markdown
# .claude/agents/orchestrator.md

当用户提出新功能需求时：
1. 并行调用 4 个 Agent（不等用户确认）
2. 收集结果
3. 创建完整方案
4. 直接开始执行第一个任务

关键：不问"要不要开始"，直接执行。
```

---

#### Feature 6: GitHub Actions 集成（定时任务）

**功能描述**:
使用 GitHub Actions 定时运行 Claude Code，自动执行 Sprint 报告、代码审查等任务。

**参考项目**:
- [ChrisWiles/claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) - PR Review Workflow
- [Anthropic/claude-code-action](https://github.com/anthropics/claude-code-action) - 官方 Action

**示例 Workflow**:
```yaml
name: Sprint Weekly Report

on:
  schedule:
    - cron: '0 10 * * MON'  # 每周一 10:00
  workflow_dispatch:  # 手动触发

jobs:
  sprint-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate Sprint Report
        uses: anthropics/claude-code-action@beta
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: claude-sonnet-4-5
          timeout_minutes: 10
          prompt: |
            生成本周 Sprint 进度报告：
            1. 读取 .scrum/sprints/current.md
            2. 统计 Issue 完成情况
            3. 生成 Markdown 报告到 docs/sprint-reports/
            4. 提交到 Git
          claude_args: |
            --max-turns 5
            --allowedTools "Read,Glob,Write,Bash(git:*)"

      - name: Commit Report
        run: |
          git config user.name "Claude Bot"
          git config user.email "claude@anthropic.com"
          git add docs/sprint-reports/
          git commit -m "docs: weekly sprint report" || echo "No changes"
          git push
```

**更多场景**:
- **每日代码审查**: 检查新提交是否符合代码质量红线
- **每周进度报告**: 汇总 Issue 统计
- **PR 自动审查**: 在 PR 创建时触发 Claude Code Review

**实现复杂度**: 简单
- 使用官方 claude-code-action
- 配置 YAML 文件
- 设置 GitHub Secrets

**适用性**: 适合
- 自动化重复性任务
- 定时生成报告
- 减少人工操作

**建议优先级**: P1（高优先级）

---

### P2 - 中优先级（改进体验）

#### Feature 7: Modular Skill Pattern（模块化 Skill）

**功能描述**:
将大型 Skill 拆分为主文件 + 资源文件，实现渐进式加载，避免超过 Context Window。

**参考项目**:
- [diet103/claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase) - 500-Line Rule

**结构模式**:
```
.claude/skills/scrum-workflow/
├── SKILL.md                    # <500 行，核心指引
├── resources/
│   ├── issue-creation.md       # <500 行，详细步骤
│   ├── sprint-planning.md
│   ├── repo-boundary-rules.md
│   └── acceptance-criteria.md
```

**SKILL.md 示例**:
```markdown
---
name: scrum-workflow
description: Scrum 工作流管理
---

# Scrum Workflow Skill

## 核心职责
- 创建和管理 Issue
- Sprint 规划
- Repo 边界检查

## 快速指引
- Issue 创建 → 查看 resources/issue-creation.md
- Sprint 规划 → 查看 resources/sprint-planning.md
- Repo 边界 → 查看 resources/repo-boundary-rules.md

## 何时使用
当用户提到：
- "创建 Issue"
- "规划 Sprint"
- "检查 Repo 边界"
```

**实现复杂度**: 简单
- 拆分现有 Skill 文件
- 使用 Read tool 按需加载资源

**适用性**: 适合
- 避免 CLAUDE.md 超过 200 行限制
- Skill 内容复杂时

**建议优先级**: P2（中优先级）

---

#### Feature 8: Slash Command + Skill 联动

**功能描述**:
用户执行 Slash Command 时，自动激活相关 Skill。

**参考项目**:
- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) - Command/Skill 最佳实践

**示例**:
```markdown
# .claude/commands/create-issue.md
---
name: create-issue
description: 创建新 Issue（自动激活 scrum-workflow skill）
---

请创建新 Issue：

1. 激活 scrum-workflow skill
2. 询问 Issue 类型、标题、描述
3. 验证 Repo 边界
4. 创建 Issue 文件
5. 运行 validate-issue.sh Hook
```

**实现复杂度**: 简单
- Slash Command 明确提示激活 Skill
- 用户体验更流畅

**适用性**: 适合
- 简化常用操作
- 新手友好

**建议优先级**: P2（中优先级）

---

### P3 - 低优先级（锦上添花）

#### Feature 9: Dev Docs System（上下文恢复）

**功能描述**:
在 Context Reset 前，自动保存关键上下文到文档，下次会话自动加载。

**参考项目**:
- [diet103/claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase) - dev/active/ 模式

**实现方式**:
```
dev/active/
├── current-sprint.md        # 当前 Sprint 状态
├── recent-decisions.md      # 最近的架构决策
├── known-issues.md          # 已知问题
└── next-steps.md            # 下一步计划
```

**Slash Command**: `/dev-docs-update`
```markdown
保存当前上下文：
1. 总结本次会话的工作
2. 更新 dev/active/current-sprint.md
3. 记录重要决策
4. 列出待办事项
```

**实现复杂度**: 简单
- 使用 Write tool 更新 Markdown 文件
- Context Reset 前手动调用

**适用性**: 一般
- 长期项目有用
- 短期 MVP 可暂缓

**建议优先级**: P3（低优先级）

---

#### Feature 10: Dashboard HTML（可视化进度）

**功能描述**:
生成 HTML Dashboard，可视化展示 Sprint 进度、Agent 执行统计、Issue 看板。

**参考项目**:
- [Dicklesworthstone/claude_code_agent_farm](https://github.com/Dicklesworthstone/claude_code_agent_farm) - HTML Run Reports

**实现方式**:
```bash
# 生成 Dashboard
python scripts/generate-dashboard.py

# 输出
docs/dashboard.html
```

**包含内容**:
- Sprint Burndown Chart（燃尽图）
- Issue 状态分布（饼图）
- Agent 执行统计（条形图）
- 最近 10 次提交（表格）

**实现复杂度**: 中等
- 需要数据聚合逻辑
- HTML/CSS/JS 可视化
- 可选：Chart.js / D3.js

**适用性**: 一般
- 演示场景有用
- 日常开发可能用不到

**建议优先级**: P3（低优先级）

---

## 2. 设计模式总结

### 2.1 Hook + MCP 协作模式

**模式**: Hook 触发 MCP 工具，实现自动化工作流

```
用户提交 Prompt
    ↓
UserPromptSubmit Hook（skill-eval.sh）
    ↓
分析 Prompt，建议 Skill
    ↓
用户批准（或自动激活）
    ↓
Skill 执行（调用 MCP 工具）
    ↓
PostToolUse Hook（追踪执行）
    ↓
Stop Hook（验收）
    ↓
如果失败 → 阻止停止 → Claude 继续修复
如果成功 → 允许停止
```

**关键点**:
- Hook 是**触发器**，MCP 是**执行器**
- Hook 不执行业务逻辑，只做拦截和验证
- MCP 工具提供核心能力（create_issue, update_status）

---

### 2.2 Agent 编排模式

**模式1: Orchestrator Pattern（中央协调）**
```
Orchestrator Agent
    ├─→ tech-intelligence-agent
    ├─→ cto-agent
    ├─→ tdd-agent
    └─→ scrum-master-agent
         └─→ 创建 Issue
```

**模式2: Pipeline Pattern（流水线）**
```
需求 → PM Agent
      ↓
  分析需求 → CTO Agent
             ↓
       设计架构 → TDD Agent
                  ↓
             编写测试 → Scrum Agent
                        ↓
                  创建 Issue
```

**模式3: Swarm Pattern（群体智能）**
```
用户需求
    ↓
多个 Agent 并行分析
    ├─→ Agent A（角度1）
    ├─→ Agent B（角度2）
    └─→ Agent C（角度3）
         ↓
   汇总结果 → 最终方案
```

**最佳实践**:
- Orchestrator 适合固定流程
- Pipeline 适合顺序依赖
- Swarm 适合探索性任务

---

### 2.3 进度追踪模式

**模式**: Markdown 表格 + JSON 统计 + 可选 HTML

```
执行 Agent/Tool
    ↓
PostToolUse Hook
    ↓
追加到 EXECUTION_LOG.md（人类可读）
    ↓
更新 tool-usage.json（机器可读）
    ↓
可选：生成 HTML Dashboard
```

**数据格式**:
- **Markdown 表格**: 人类友好，Git Diff 友好
- **JSON**: 机器可读，统计分析
- **HTML**: 可视化展示

**关键指标**:
- 执行时间戳
- Agent/Tool 名称
- 状态（COMPLETE/ERROR/PARTIAL）
- 耗时
- 结果摘要

---

### 2.4 工作流定义模式

**Workflow Markdown 格式**:
```markdown
---
name: sprint-planning-workflow
description: Sprint 规划工作流
agents: [scrum-master, cto-agent, tdd-agent]
---

# Sprint Planning Workflow

## Steps:
1. scrum-master: 创建 Sprint 文件
2. cto-agent: 分析技术依赖
3. tdd-agent: 设计验收标准
4. scrum-master: 分配 Issue 到 Sprint

## Trigger:
- 用户说："开始 Sprint 规划"
- 每月第一个周一 10:00（GitHub Actions）

## Output:
- Sprint 文件：.scrum/sprints/2026-W10.md
- Issue 列表：.scrum/issues/...
```

**执行方式**:
- 手动：`/sprint-planning` Slash Command
- 自动：GitHub Actions Cron

---

### 2.5 Skill 激活模式

**规则引擎模式**:
```javascript
// skill-rules.json
{
  "skills": {
    "skill-name": {
      "triggers": {
        "keywords": ["word1", "word2"],
        "keywordPatterns": ["regex1", "regex2"],
        "pathPatterns": ["**/*.md", "src/**"],
        "intentPatterns": ["create.*issue", "plan.*sprint"],
        "directoryMappings": {
          ".scrum/issues": "scrum-workflow"
        }
      },
      "priority": 9
    }
  },
  "scoring": {
    "keyword": 2,
    "keywordPattern": 3,
    "pathPattern": 4,
    "directoryMatch": 5,
    "intentPattern": 4
  }
}
```

**评分算法**:
```
总分 = Σ(匹配项数量 × 权重)
激活阈值 = 3分
建议 Top 3 Skill
```

---

## 3. 避坑指南

### 3.1 Hook 常见错误

#### 错误1: Stop Hook 无限循环

**问题**:
```bash
Stop Hook 阻止 Claude 停止
→ Claude 尝试修复
→ 再次触发 Stop Hook
→ 再次阻止
→ 无限循环
```

**解决方案**:
```bash
#!/bin/bash
# 检查 stop_hook_active 变量
if [[ "$CLAUDE_STOP_HOOK_ACTIVE" == "true" ]]; then
  # Claude 已经尝试过停止，不再阻止
  exit 0
fi

# 执行验收检查
if [[ 验收失败 ]]; then
  echo '{"block": true, "message": "请修复..."}' >&2
  exit 2
fi
```

---

#### 错误2: Hook 超时阻塞

**问题**:
Hook 执行时间过长，拖慢 Claude 响应速度。

**解决方案**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "expensive-operation.sh",
        "timeout": 5  // 设置合理超时（秒）
      }
    ]
  }
}
```

**建议超时**:
- Command Hook: 2-5 秒
- Prompt Hook: 5-10 秒
- Agent Hook: 10-30 秒

---

#### 错误3: 过度使用 Prompt Hook

**问题**:
所有验证都用 Prompt Hook，消耗大量 Token，响应慢。

**解决方案**:
**优先级**: Command Hook > Prompt Hook > Agent Hook

```
能用 shell 脚本验证的 → Command Hook
需要语义判断的 → Prompt Hook
需要读取多个文件的 → Agent Hook
```

---

### 3.2 MCP 工具常见错误

#### 错误1: 工具命名不规范

**问题**:
```python
# 错误
@mcp.tool()
def create_issue():
    pass

# 工具名变成: create_issue
# 应该是: mcp__scrum__create_issue
```

**解决方案**:
遵循命名约定：`mcp__<server-name>__<tool-name>`

---

#### 错误2: 权限过于宽松

**问题**:
```json
{
  "allowedTools": ["*"]  // 允许所有工具
}
```

**解决方案**:
```json
{
  "allowedTools": [
    "Read",
    "Write",
    "Bash(git:*)",
    "mcp__scrum__*"  // 只允许 scrum 相关工具
  ]
}
```

---

### 3.3 Agent 常见错误

#### 错误1: Agent Markdown 过长

**问题**:
单个 Agent 文件超过 2000 行，超过 Context Window。

**解决方案**:
- 拆分为 AGENT.md + resources/
- AGENT.md < 500 行
- 按需加载 resources

---

#### 错误2: Agent 职责不清

**问题**:
多个 Agent 功能重叠，互相冲突。

**解决方案**:
- 明确每个 Agent 的 `description` 字段
- 使用 `when to use` 和 `when NOT to use` 章节
- Orchestrator 协调，避免直接调用

---

### 3.4 Skill 常见错误

#### 错误1: Skill 不会自动激活

**问题**:
创建了 Skill，但 Claude 从不使用。

**解决方案**:
1. 添加 UserPromptSubmit Hook（skill-eval）
2. 配置 skill-rules.json
3. 确保 Skill 的 `description` 清晰

---

#### 错误2: Skill 触发条件过于宽泛

**问题**:
```json
{
  "triggers": {
    "keywords": ["code", "file", "test"]  // 太常见
  }
}
```

每次都建议激活，造成干扰。

**解决方案**:
- 使用更具体的关键词
- 结合 intentPatterns 精确匹配
- 提高激活阈值（minConfidenceScore: 5）

---

## 4. 实现路线图建议

### Phase 0: 核心基础（1-2 周）

**目标**: 建立基础设施，立即提升效率

#### Week 1: 进度追踪 + 基础 Hooks

**任务**:
1. **实现 EXECUTION_LOG.md** (P0)
   - 创建 Markdown 表格格式
   - MCP 工具自动追加记录
   - 统计执行成功率
   - **验收**: 手动运行一个工具，自动记录到 Log

2. **实现 validate-issue.sh Hook** (P0)
   - 检查 Issue 文件路径
   - 检查文件名格式
   - 检查 YAML Front Matter
   - **验收**: 创建不合规 Issue，Hook 阻止

3. **配置 PostToolUse Hook** (P1)
   - 追踪 MCP 工具调用
   - 生成 tool-usage.json
   - **验收**: 查看工具统计报告

**交付物**:
- `.scrum/progress/execution-log.md`
- `.claude/hooks/validate-issue.sh`
- `.claude/hooks/track-tool-usage.sh`
- `.claude/settings.json`（Hook 配置）

**预期效果**:
- 用户可随时查看进度
- AI 无法创建不合规 Issue
- 了解工具使用情况

---

#### Week 2: Skill Auto-Activation

**任务**:
1. **实现 skill-eval.js 引擎** (P0)
   - 关键词匹配
   - 意图模式检测
   - 评分算法
   - **验收**: 输入 "创建 Issue"，建议激活 scrum-workflow

2. **配置 skill-rules.json** (P0)
   - 定义 4 个 Skill 的触发规则
   - 调优评分权重
   - **验收**: 多场景测试激活准确率

3. **集成 UserPromptSubmit Hook** (P0)
   - 拦截用户输入
   - 调用 skill-eval.js
   - 输出建议
   - **验收**: 自动建议 Skill，不需手动触发

**交付物**:
- `.claude/hooks/skill-eval.js`
- `.claude/hooks/skill-eval.sh`
- `.claude/hooks/skill-rules.json`

**预期效果**:
- AI 自动激活相关 Skill
- 减少用户手动操作
- 提高工作效率

---

### Phase 1: Agent 编排（2-3 周）

**目标**: 实现多 Agent 自动协作

#### Week 3-4: Orchestrator Agent

**任务**:
1. **创建 orchestrator.md** (P1)
   - 定义 Agent 协调逻辑
   - 并行调用多个 Agent
   - 汇总结果
   - **验收**: 用户说"实现功能X"，自动调用 4 个 Agent

2. **优化现有 4 个 Agent** (P1)
   - 统一输出格式
   - 明确职责边界
   - 添加 `when to use` 章节
   - **验收**: Agent 输出可被 Orchestrator 解析

3. **实现 Task tool 集成** (P1)
   - Orchestrator 调用子 Agent
   - 子 Agent 返回结构化结果
   - **验收**: 并行调用 3 个 Agent，5 分钟内完成

**交付物**:
- `.claude/agents/orchestrator.md`
- 优化后的 `cto-agent.md`, `tech-intelligence-agent.md`, `tdd-agent.md`, `scrum-master.md`

**预期效果**:
- 用户一句话触发完整工作流
- AI 自动分配任务
- 减少手动协调

---

#### Week 5: Stop Hook 验收链

**任务**:
1. **实现 validate-ac.sh** (P0)
   - 检查 AC 是否符合 SMART 原则
   - 使用 Prompt Hook
   - **验收**: 创建缺少 AC 的 Issue，Hook 阻止

2. **实现 validate-repo-boundary.sh** (P0)
   - 检查是否跨 Repo 修改
   - 使用 Command Hook
   - **验收**: 尝试修改多个 Repo，Hook 阻止

3. **链式 Hook 验收** (P0)
   - Stop Hook 串联多个验收
   - 按优先级执行
   - **验收**: 运行完整验收链，确保质量

**交付物**:
- `.claude/hooks/validate-ac.sh`
- `.claude/hooks/validate-repo-boundary.sh`
- 更新 `.claude/settings.json`（Hook 链配置）

**预期效果**:
- AI 无法提交不合规代码
- 强制执行 CLAUDE.md 约束
- 自动化质量保证

---

### Phase 2: 自动化与集成（2-3 周）

**目标**: GitHub Actions 集成，定时任务

#### Week 6-7: GitHub Actions

**任务**:
1. **实现 Sprint Weekly Report** (P1)
   - GitHub Actions Cron
   - 调用 Claude Code
   - 生成 Markdown 报告
   - 自动提交 Git
   - **验收**: 手动触发 Workflow，生成报告

2. **实现 PR Code Review** (P1)
   - PR 创建时触发
   - Claude 审查代码
   - 评论到 PR
   - **验收**: 创建测试 PR，自动审查

3. **实现 Daily Quality Check** (P1)
   - 每日检查代码质量红线
   - 生成报告
   - 发送通知
   - **验收**: 查看每日报告

**交付物**:
- `.github/workflows/sprint-weekly-report.yml`
- `.github/workflows/pr-code-review.yml`
- `.github/workflows/daily-quality-check.yml`

**预期效果**:
- 自动化重复性任务
- 定时生成报告
- 减少人工操作

---

#### Week 8: Dashboard（可选）

**任务**:
1. **生成 HTML Dashboard** (P3)
   - 聚合数据（EXECUTION_LOG, tool-usage, Issue）
   - 可视化图表
   - **验收**: 打开 Dashboard，查看进度

2. **集成到 Sprint Report** (P3)
   - GitHub Actions 自动生成
   - 部署到 GitHub Pages
   - **验收**: 访问在线 Dashboard

**交付物**:
- `scripts/generate-dashboard.py`
- `docs/dashboard.html`
- `.github/workflows/deploy-dashboard.yml`

**预期效果**:
- 可视化进度展示
- 演示友好

---

### Phase 3: 高级功能（按需）

#### 可选功能（不紧急）

1. **Dev Docs System** (P3)
   - Context Reset 恢复
   - 适合长期项目

2. **Modular Skill Pattern** (P2)
   - 当 Skill 文件过大时实施
   - 500-Line Rule

3. **Swarm Intelligence** (P3)
   - 多 Agent 并行探索
   - 适合复杂决策

---

## 5. 快速启动检查清单

### 立即实施（本周）

- [ ] 创建 `.scrum/progress/execution-log.md`
- [ ] 实现 `validate-issue.sh` Hook
- [ ] 配置 `.claude/settings.json`
- [ ] 测试 Stop Hook 阻止机制

### 下周实施

- [ ] 实现 `skill-eval.js` 引擎
- [ ] 配置 `skill-rules.json`
- [ ] 测试 Skill Auto-Activation

### 两周后实施

- [ ] 创建 Orchestrator Agent
- [ ] 优化现有 4 个 Agent
- [ ] 测试多 Agent 协作

---

## 6. 社区资源链接

### 顶级项目（必看）

1. **awesome-claude-code** (26721★)
   - https://github.com/hesreallyhim/awesome-claude-code
   - 最全面的资源列表

2. **claude-code-infrastructure-showcase** (9189★)
   - https://github.com/diet103/claude-code-infrastructure-showcase
   - Skill Auto-Activation 最佳实践

3. **claude-code-showcase** (5455★)
   - https://github.com/ChrisWiles/claude-code-showcase
   - 完整项目配置示例

4. **claude-code-hooks-mastery** (3238★)
   - https://github.com/disler/claude-code-hooks-mastery
   - Hooks 权威指南

### 官方文档

- Claude Code Hooks: https://code.claude.com/docs/en/hooks-guide
- Agent Teams: https://code.claude.com/docs/en/agent-teams
- MCP Integration: https://code.claude.com/docs/en/mcp
- GitHub Actions: https://code.claude.com/docs/en/github-actions

### 社区博客

- Hooks Practical Guide: https://wmedia.es/en/writing/claude-code-hooks-practical-guide
- MCP Tools Integration: https://scottspence.com/posts/configuring-mcp-tools-in-claude-code
- Slash Commands Guide: https://alexop.dev/posts/claude-code-slash-commands-guide/

---

## 7. 总结与建议

### 最值得实施的 3 个功能

1. **EXECUTION_LOG.md** (P0) - 立即可见的价值
2. **Stop Hook 验收** (P0) - 防止低级错误
3. **Skill Auto-Activation** (P0) - 显著提升效率

### 最容易踩的 3 个坑

1. **Stop Hook 无限循环** - 记得检查 `stop_hook_active`
2. **Skill 不会激活** - 必须配置 UserPromptSubmit Hook
3. **过度使用 Prompt Hook** - 优先用 Command Hook

### 最佳实践原则

1. **Hook 是触发器，MCP 是执行器** - 职责分离
2. **Command Hook > Prompt Hook > Agent Hook** - 性能优先
3. **Markdown 表格 + JSON 统计** - 人机双可读
4. **500-Line Rule** - 避免超过 Context Window
5. **Orchestrator 协调，Agent 执行** - 中央调度

---

**报告完成时间**: 2026-03-08
**调研总时长**: 约 45 分钟
**参考项目数量**: 10+
**提取 Features 数量**: 10
**设计模式数量**: 5
**避坑指南条目**: 10+

建议优先实施 P0 功能，快速验证价值，再逐步扩展到 P1/P2 功能。
