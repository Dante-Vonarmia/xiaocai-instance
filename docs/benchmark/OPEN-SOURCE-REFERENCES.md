# 开源项目参考清单 · 小采 1.0

**文档版本**: v1.0
**最后更新**: 2026-02-08
**目的**: 收集高质量开源项目，辅助项目开发，避免重复造轮子

---

## 一、LangGraph 生产级应用

### 1.1 官方资源（必看）

#### **langchain-ai/langgraph** ⭐ 核心仓库
- **URL**: https://github.com/langchain-ai/langgraph
- **用途**: LangGraph 核心库，构建有状态的 Agent 应用
- **生产案例**: Klarna, Replit, Elastic
- **可复用部分**:
  - Checkpoint 机制（状态持久化）
  - StateGraph 状态机
  - 内置的流式输出（`astream_events`）

#### **langchain-ai/langgraph-supervisor-py** ⭐⭐⭐ 重点参考
- **URL**: https://github.com/langchain-ai/langgraph-supervisor-py
- **用途**: Supervisor 模式实现 - 多 Agent 协调
- **核心模式**:
  ```python
  # 创建 Supervisor 管理多个 Agent
  workflow = create_supervisor(
      [research_agent, math_agent],
      model=model,
      prompt="You are a team supervisor managing experts."
  )
  ```
- **可复用部分**:
  - Supervisor Agent 实现
  - Agent 间消息传递机制
  - 动态 Agent 切换逻辑
  - 消息历史管理模式（full_history / last_message）

**直接应用到小采项目**:
- 用 Supervisor 模式管理我们的 Greeter、Requirement、Search 等 Agent
- 借鉴消息路由机制
- 参考 Agent handoff 工具实现

---

#### **langchain-ai/langgraph-swarm-py**
- **URL**: https://github.com/langchain-ai/langgraph-swarm-py
- **用途**: Swarm 模式 - 多 Agent 协作
- **适用场景**: 需要多个 Agent 并行处理任务

#### **von-development/awesome-LangGraph**
- **URL**: https://github.com/von-development/awesome-LangGraph
- **用途**: LangGraph 生态系统索引
- **包含**: 概念、项目、工具、模板、指南

### 1.2 生产级示例

#### **expectbugs/agents** ⭐⭐ 生产级参考
- **URL**: https://github.com/expectbugs/agents
- **用途**: 生产级多 Agent 系统，带持久化和 Web 搜索
- **特点**:
  - Multi-Agent 协同
  - 持久化内存
  - Web 搜索集成
- **可复用部分**:
  - 整体架构设计
  - Agent 协调模式
  - 状态管理方案

#### **google-gemini/gemini-fullstack-langgraph-quickstart**
- **URL**: https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart
- **用途**: 全栈 LangGraph 应用（React + LangGraph 后端）
- **可复用部分**:
  - 前后端集成方式
  - API 设计模式

---

## 二、SSE 流式对话实现

### 2.1 生产级 SSE 库

#### **sysid/sse-starlette** ⭐⭐⭐ 强烈推荐
- **URL**: https://github.com/sysid/sse-starlette
- **用途**: 生产级 SSE 实现，符合 W3C 规范
- **特点**:
  - 自动客户端断开检测
  - 线程安全
  - 多 asyncio 事件循环支持
- **核心代码**:
  ```python
  from sse_starlette.sse import EventSourceResponse

  async def stream_data(request):
      events_sent = 0
      try:
          while events_sent < 100:
              # 检测客户端断开
              if await request.is_disconnected():
                  print(f"Client disconnected after {events_sent} events")
                  break

              yield {"data": f"Event {events_sent}", "event": "update"}
              events_sent += 1
              await asyncio.sleep(1)
      except Exception as e:
          print(f"Error: {e}")

  return EventSourceResponse(stream_data(request))
  ```

**直接应用到小采项目**:
- 替换我们自己实现的 SSE 流式推送
- 使用 `is_disconnected()` 检测客户端状态
- 复用线程安全的实现

---

#### **talesmousinho/fastapi-openai-sse-stream**
- **URL**: https://github.com/talesmousinho/fastapi-openai-sse-stream
- **用途**: FastAPI + OpenAI SSE 流式响应
- **可复用部分**:
  - OpenAI API 流式调用模式
  - SSE 事件格式化

### 2.2 实战示例

#### **LangChain QA Chatbot Streaming** ⭐⭐ 完整示例
- **URL**: https://gist.github.com/jvelezmagic/f3653cc2ddab1c91e86751c8b423a1b6
- **用途**: QA 聊天机器人，带 SSE 流式输出
- **技术栈**: FastAPI + LangChain + OpenAI + Chroma
- **可复用部分**:
  - 完整的聊天流程实现
  - Source documents 展示
  - 流式输出格式

---

## 三、Agent 提示词工程

### 3.1 提示词资源库

#### **dair-ai/Prompt-Engineering-Guide** ⭐⭐⭐ 必读
- **URL**: https://github.com/dair-ai/Prompt-Engineering-Guide
- **网站**: https://www.promptingguide.ai
- **用途**: 提示词工程综合指南
- **包含**:
  - RAG 最佳实践
  - AI Agents 提示词模式
  - Context Engineering

#### **tallesborges/agentic-system-prompts** ⭐⭐ 生产级提示词
- **URL**: https://github.com/tallesborges/agentic-system-prompts
- **用途**: 真实生产环境的 Agent 系统提示词
- **包含**: 各种 AI Coding Agents 的系统提示词和工具定义
- **价值**: "What makes agentic coding applications different? TBH, it's mostly their system prompts."

#### **dontriskit/awesome-ai-system-prompts** ⭐⭐⭐ 顶级 AI 工具提示词
- **URL**: https://github.com/dontriskit/awesome-ai-system-prompts
- **用途**: 顶级 AI 工具的系统提示词集合
- **包含**: ChatGPT, Claude, Perplexity, v0, Cursor 等

### 3.2 提示词模式参考

#### **Vercel v0 模式**（UI 生成 Agent）
```markdown
核心特点:
- 使用 MDX 组件作为"工具"（如 <CodeProject>、<QuickEdit>）
- 高度领域特定的规则（Next.js、Tailwind）
- 强制 <Thinking> 阶段（规划后再生成）

结构:
1. 角色定义
2. 领域规则
3. 工具定义
4. 思考-生成流程
```

**直接应用到小采项目**:
- 为每个 Agent 添加 `<Thinking>` 阶段
- 使用结构化标签组织提示词
- 明确领域规则（采购流程、字段定义）

---

#### **same.new 模式**（Pair Programming Agent）
```markdown
核心特点:
- 使用 XML 标签组织规则（<tool_calling>、<web_development>）
- 严格的工具使用指南
- 迭代式工作流程

关键约束:
- "NEVER refer to tool names when speaking to the USER"
- 先解释工具调用原因，再调用
- 错误修正机制
```

**直接应用到小采项目**:
- 约束 Agent 不要暴露内部工具名称
- 强制解释每一步操作的原因
- 实现错误自我修正机制

---

#### **Manus 模式**（通用 Agent）
```markdown
核心特点:
- 明确的 Agent 循环定义:
  1. Analyze Events
  2. Select Tools
  3. Wait for Execution
  4. Iterate (单次工具调用)
  5. Submit Results

结构:
- 明确的环境上下文
- 详细的沙盒环境说明
- 步骤化的推理流程
```

**直接应用到小采项目**:
- 为每个 Agent 定义清晰的执行循环
- 提供环境上下文（可用字段、历史数据）
- 强制单步工具调用（避免一次性调用多个工具）

---

### 3.3 提示词最佳实践（2024-2025）

#### **核心原则**

1. **明确 AI 身份**
   ```
   You are a Procurement Requirement Agent.
   Your role: Extract 9 required fields from user input.
   Your domain: Procurement requests in Chinese enterprises.
   ```

2. **嵌入领域知识**
   ```
   Domain Knowledge:
   - 项目类别: IT设备、办公用品、原材料
   - 必填字段: 项目名称、背景、类别、数量、预算、交付时间、地点、描述、特殊要求
   - 常见配置: 办公电脑 = CPU + 内存 + 硬盘 + 操作系统
   ```

3. **结构化输出约束**
   ```
   Output Format (JSON):
   {
     "fields_extracted": {
       "项目名称": "...",
       "项目背景": "...",
       ...
     },
     "missing_fields": ["交付时间", "预算"],
     "next_question": "请问您的预算范围是多少？"
   }
   ```

4. **使用标签组织规则**
   ```markdown
   <role>
   You are a Requirement Agent.
   </role>

   <capabilities>
   - Extract fields from natural language
   - Generate follow-up questions
   - Validate completeness
   </capabilities>

   <constraints>
   - NEVER make up information
   - ALWAYS ask before assuming
   - Keep responses concise (< 100 words)
   </constraints>
   ```

---

## 四、LangGraph 状态管理与持久化

### 4.1 官方文档

#### **LangGraph Persistence** ⭐⭐⭐ 官方指南
- **URL**: https://langchain-ai.github.io/langgraph/how-tos/persistence-functional/
- **核心概念**:
  - Checkpointer: 保存每个 super-step 的状态
  - Thread ID: 主键，用于存储和恢复状态
  - Time-travel: 回到任意历史状态

#### **核心代码**:
```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 创建 checkpointer
memory = SqliteSaver.from_conn_string(":memory:")

# 编译图
graph = workflow.compile(checkpointer=memory)

# 执行时传入 thread_id
config = {"configurable": {"thread_id": "session-123"}}
result = graph.invoke(input, config=config)
```

**直接应用到小采项目**:
- 使用内置 Checkpointer 替代自研状态管理
- 用 thread_id 管理会话
- 支持对话历史回溯

---

### 4.2 Redis 集成

#### **LangGraph + Redis**
- **URL**: https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/
- **GitHub**: https://github.com/redis-developer/langgraph-redis
- **用途**: 使用 Redis 作为 Checkpointer 后端
- **优势**:
  - 更快的读写速度
  - 支持分布式部署
  - TTL 自动清理

---

## 五、可直接复用的代码模式

### 5.1 LangGraph Supervisor 创建

```python
from langgraph.prebuilt import create_supervisor

# 定义专业 Agents
research_agent = create_agent(model, tools, "You are a research expert.")
requirement_agent = create_agent(model, tools, "You are a requirement analyst.")

# 创建 Supervisor
supervisor_workflow = create_supervisor(
    agents=[research_agent, requirement_agent],
    model=model,
    prompt="You are a team supervisor. Route tasks to the right expert.",
    history_mode="last_message"  # 或 "full_history"
)

# 编译
app = supervisor_workflow.compile()

# 执行
result = app.invoke({"messages": [HumanMessage(content="用户输入")]})
```

**应用到小采**:
- 替换我们手动实现的 Agent 路由
- 使用 `create_supervisor` 管理 5 个 Agent
- 配置 `history_mode` 控制上下文传递

---

### 5.2 SSE 流式推送（生产级）

```python
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/stream")
async def stream_thinking(request: Request, session_id: str):
    async def event_generator():
        try:
            # 订阅 Redis Pub/Sub
            pubsub = redis.pubsub()
            await pubsub.subscribe(f"session:{session_id}:thinking")

            async for message in pubsub.listen():
                # 检测客户端断开
                if await request.is_disconnected():
                    await pubsub.unsubscribe()
                    break

                if message["type"] == "message":
                    yield {
                        "event": "thinking",
                        "data": message["data"]
                    }
        finally:
            await pubsub.close()

    return EventSourceResponse(event_generator())
```

**应用到小采**:
- 替换我们自己实现的 SSE
- 添加客户端断开检测
- 实现自动资源清理

---

### 5.3 Agent 提示词模板（结构化）

```python
REQUIREMENT_AGENT_PROMPT = """
<role>
You are a Procurement Requirement Agent for Chinese enterprises.
</role>

<task>
Extract 9 required fields from user's procurement request:
1. 项目名称 (Project Name)
2. 项目背景和目的 (Background & Purpose)
3. 项目类别 (Category)
4. 交付时间 (Delivery Date)
5. 交付地点 (Delivery Location)
6. 数量和单位 (Quantity & Unit)
7. 预算 (Budget)
8. 项目需求具体描述 (Detailed Description)
9. 特殊要求 (Special Requirements)
</task>

<thinking_process>
Before responding, follow these steps:
1. Identify which fields are already provided
2. Determine which fields are missing
3. Generate ONE focused follow-up question
4. Format response as JSON
</thinking_process>

<constraints>
- NEVER make up information
- ALWAYS ask ONE question at a time
- Keep responses concise (< 100 words in Chinese)
- Use JSON format for structured output
</constraints>

<output_format>
{{
  "fields_extracted": {{
    "项目名称": "..." or null,
    "项目背景": "..." or null,
    ...
  }},
  "completeness": 0.67,  # 6/9 fields filled
  "missing_fields": ["交付时间", "预算", "特殊要求"],
  "next_question": "请问您的预算范围是多少？",
  "user_friendly_response": "我理解您需要采购办公电脑。为了给您更精准的建议，请问您的预算范围是多少？"
}}
</output_format>

<examples>
User: "需要100台办公电脑"
Assistant: {{
  "fields_extracted": {{
    "项目类别": "IT设备 > 办公电脑",
    "数量和单位": "100台"
  }},
  "completeness": 0.22,
  "missing_fields": ["项目名称", "背景", "交付时间", "地点", "预算", "描述", "特殊要求"],
  "next_question": "请问这个采购项目的名称是什么？（例如：研发部办公电脑采购）",
  "user_friendly_response": "我理解您需要采购100台办公电脑。请问这个采购项目的名称是什么？"
}}
</examples>
"""
```

**应用到小采**:
- 复制此模板结构
- 为每个 Agent 定制 `<role>`、`<task>`、`<constraints>`
- 统一 `<output_format>` 为 JSON Schema

---

### 5.4 LangGraph 状态持久化

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

# Phase 0: 内存
memory = SqliteSaver.from_conn_string(":memory:")

# Phase 1: SQLite 文件
memory = SqliteSaver.from_conn_string("checkpoints.db")

# 编译图
graph = workflow.compile(checkpointer=memory)

# 执行（自动保存状态）
config = {
    "configurable": {
        "thread_id": f"session-{session_id}",
        "checkpoint_ns": "xiaocai"
    }
}

# 首次执行
result = graph.invoke({"messages": [...]}, config=config)

# 恢复执行（自动加载历史状态）
result = graph.invoke({"messages": [...]}, config=config)
```

**应用到小采**:
- Phase 0: 用内存 Checkpointer
- Phase 1: 切换到 SQLite 文件
- 删除我们自研的状态管理代码

---

## 六、本地开发流程优化

### 6.1 LangSmith 集成（零代码）

**官方监控工具** - 替代自研 AI 透明化

```bash
# .env 文件
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=xiaocai-1.0
```

**自动获得**:
- Agent 执行轨迹
- Token 消耗统计
- 性能分析
- 错误追踪
- 可视化调试

**无需编写任何代码**！

---

### 6.2 开发环境配置

#### **推荐工具链**
```bash
# Python 环境管理
uv  # 替代 pip, poetry（快10倍）

# 代码质量
ruff  # 替代 black + flake8 + isort（快100倍）

# 测试
pytest + pytest-asyncio

# 类型检查
pyright  # 替代 mypy（更快更准确）
```

#### **LangGraph 开发服务器**
```bash
# 官方开发服务器（带 Hot Reload）
langgraph dev

# 自动提供:
# - HTTP API
# - WebSocket 调试
# - 可视化界面
```

---

## 七、项目特定应用建议

### 7.1 立即可做的优化

#### **1. 使用 LangGraph Supervisor**
```python
# 当前: 手动实现 Agent 路由
# 改进: 使用 create_supervisor

from langgraph.prebuilt import create_supervisor

supervisor = create_supervisor(
    [greeter_agent, requirement_agent, search_agent],
    model=model,
    prompt="You manage procurement agents. Route to: greeter (initial contact), requirement (extract fields), search (find suppliers)."
)
```

#### **2. 使用 sse-starlette 库**
```python
# 当前: 自己实现 SSE
# 改进: 用生产级库

from sse_starlette.sse import EventSourceResponse

@app.get("/thinking-stream")
async def thinking_stream(request: Request, session_id: str):
    return EventSourceResponse(event_generator(request, session_id))
```

#### **3. 使用 LangGraph 内置 Checkpoint**
```python
# 当前: 自己管理状态
# 改进: 用内置 Checkpointer

from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")
graph = workflow.compile(checkpointer=memory)
```

#### **4. 采用结构化提示词模板**
```python
# 当前: 提示词散落在代码中
# 改进: 用结构化模板

from pathlib import Path

PROMPTS_DIR = Path("prompts/")

requirement_prompt = (PROMPTS_DIR / "requirement_agent.md").read_text()
search_prompt = (PROMPTS_DIR / "search_agent.md").read_text()
```

---

### 7.2 Phase 0 推荐技术栈调整

**当前技术栈**:
- LangGraph 0.2.x ✅
- FastAPI ✅
- 自研 SSE ❌
- 自研状态管理 ❌
- 自研 AI 透明化 ❌

**推荐技术栈**:
- LangGraph 0.2.x ✅（保持）
- FastAPI ✅（保持）
- **sse-starlette** ⭐ 新增
- **LangGraph Checkpointer** ⭐ 新增
- **LangSmith** ⭐ 新增（可选）

**预期效果**:
- 删除 500+ 行自研代码
- 提升稳定性和性能
- 获得更好的开发体验

---

## 八、GitHub Stars 总结

| 项目 | Stars | 用途 | 优先级 |
|------|-------|------|--------|
| langchain-ai/langgraph | 17.5k+ | LangGraph 核心库 | ⭐⭐⭐ |
| dair-ai/Prompt-Engineering-Guide | 48k+ | 提示词工程指南 | ⭐⭐⭐ |
| sysid/sse-starlette | 500+ | 生产级 SSE 库 | ⭐⭐⭐ |
| dontriskit/awesome-ai-system-prompts | 3k+ | 顶级 AI 工具提示词 | ⭐⭐⭐ |
| langchain-ai/langgraph-supervisor-py | - | Supervisor 模式 | ⭐⭐⭐ |
| tallesborges/agentic-system-prompts | 200+ | 生产级 Agent 提示词 | ⭐⭐ |
| expectbugs/agents | 100+ | 生产级多 Agent 系统 | ⭐⭐ |

---

## 九、下一步行动

### 9.1 立即可做（本周）

1. **安装 sse-starlette**
   ```bash
   pip install sse-starlette
   ```

2. **阅读 LangGraph Supervisor 文档**
   - https://github.com/langchain-ai/langgraph-supervisor-py

3. **研究提示词模板**
   - https://github.com/dontriskit/awesome-ai-system-prompts

### 9.2 短期计划（2周）

1. **重构 SSE 实现**
   - 使用 sse-starlette 替代自研代码

2. **采用 LangGraph Checkpointer**
   - 删除自研状态管理

3. **优化 Agent 提示词**
   - 使用结构化模板
   - 添加 `<Thinking>` 阶段

### 9.3 中期计划（Phase 1）

1. **集成 LangSmith**
   - 替代自研 AI 透明化

2. **使用 Supervisor 模式**
   - 简化 Agent 协调逻辑

---

**文档状态**: ✅ 已完成
**维护者**: 技术团队
**最后更新**: 2026-02-08
