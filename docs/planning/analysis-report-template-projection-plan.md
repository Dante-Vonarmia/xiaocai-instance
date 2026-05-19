# 分析报告模板投影串联计划

状态：Done  
Owner：xiaocai 后端 / AI 工程  
日期：2026-05-19  
关联任务：TASK-CHAT-005

验收记录：

- 测试命令：`.venv/bin/python -m pytest adapters/http_api/tests/test_analysis_content_schema_rules.py adapters/http_api/tests/test_chat_downstream_projection.py -q`
- 结果：`16 passed in 0.79s`
- 截图证据：`/var/folders/9g/23dgm0mj1sbc2g4wndwk9cr80000gn/T/TemporaryItems/NSIRD_screencaptureui_bc66am/Screenshot 2026-05-19 at 21.45.45.png`

## 1. 背景

当前产品能力已经具备：

- 设置中心可维护需求分析 prompt 模板。
- domain-pack 已提供需求分析与 RFX 策略章节模板。
- chat 流程可在右侧工作台展示 `analysis_payload`。
- 模型在左侧对话中已经能生成较符合用户预期的 RFQ / RFX 报告格式。

但当前链路没有完全串起来：

1. 左侧模型回复会受 prompt 设置影响。
2. 右侧分析报告由 xiaocai 本地投影重新生成。
3. 本地投影只复用章节名称和少量字段，没有复用用户配置的输出格式要求。
4. 当模型输出包含内部工作流语义时，右侧报告缺少统一的用户可见过滤。

因此用户看到的右侧报告可能出现：

- 格式不符合已配置模板。
- 已可推断的信息仍显示待确认。
- 内部代码、节点、步骤概念泄漏到用户界面。

## 2. 目标

将需求分析报告输出收敛为明确的产品级投影链路：

```text
设置中心 prompt 模板 / domain-pack 分析模板
→ 字段与上下文归一化
→ 报告展示结构渲染
→ 用户可见内容清洗
→ analysis_payload / markdown
```

完成后，右侧分析报告应满足：

- 按用户配置和 domain-pack 章节顺序输出。
- 对 RFQ / RFX 报告使用可读的业务格式：编号章节、表格、清单、里程碑、假设和待补充项。
- 利用已确认字段、消息抽取字段、品类推断、证据引用和模型已生成内容填充报告。
- 不将推断内容写回 confirmed truth。
- 不在用户可见内容中出现内部代码、工作流节点或 AI 自我解释。

## 3. 非目标

本任务不做以下事情：

- 不改 FLARE kernel / session / stream runtime。
- 不新增底层 workflow engine。
- 不让前端发明 authoritative state。
- 不把模型原文直接当成产品真状态。
- 不把配置中心扩展成完整模板设计器。
- 不调整现有数据库 schema。

## 4. 用户可见内容规则

### 4.1 禁止出现的内部语义

用户可见的报告正文、标题、摘要、下一步动作、工作台提示中不得出现：

- 内部函数名、节点名、动作 key。
- 英文代码式状态或任务名。
- 模型自我解释，如“我是根据流程节点生成”“当前步骤是”。
- 调试语义，如“任务推进状态”“最终目标”“当前步骤”。
- 任何无法被业务用户理解的编排概念。

### 4.2 替代表达

内部语义必须转为业务语言：

| 内部语义类型 | 用户可见表达 |
|---|---|
| 输出执行动作 | 生成采购分析报告 |
| 当前内部步骤 | 当前建议 |
| 最终内部目标 | 交付目标 |
| 工作流节点 | 采购流程阶段 |
| 代码式 key | 中文业务动作 |

### 4.3 投影与真状态分离

- 可推断内容只能进入报告展示投影。
- 只有用户明确确认或 canonical intake state 已确认的字段，才可进入 confirmed fields。
- 报告中对非确认内容使用“按当前上下文判断”“建议按此口径复核”等业务表达。

## 5. 建议实现边界

### 5.1 只改 xiaocai instance 层

优先修改：

- `adapters/http_api/src/xiaocai_instance_api/chat/analysis_projection.py`
- `adapters/http_api/src/xiaocai_instance_api/chat/analysis_content.py`
- `adapters/http_api/tests/test_chat_downstream_projection.py`
- `adapters/http_api/tests/test_analysis_content_schema_rules.py`

可选新增小文件：

- `adapters/http_api/src/xiaocai_instance_api/chat/analysis_visibility.py`

该文件只负责用户可见文本清洗，不承接字段推断、模板选择或业务决策。

### 5.2 不建议修改

- 不修改 `router.py` 中 stream 主流程，除非只是接入清洗函数。
- 不修改前端组件来兜底过滤内容。
- 不修改 FLARE 相关包。
- 不修改 provider / persistence 层。

## 6. 详细开发任务

### CHAT-005-A：审计当前报告投影输入

文件范围：

- `analysis_projection.py`
- `analysis_content.py`
- 相关测试文件

要求：

1. 明确 `build_analysis_report_projection` 当前输入来源：
   - `kernel_context.confirmed_fields`
   - `kernel_context.domain_prior.message_extracted_fields`
   - `domain_prior.category_prior.resolved_path`
   - `context_refs`
   - `domain_prompt_templates`
   - `assistant_message`
2. 确认哪些内容属于 authoritative state，哪些只可用于展示投影。
3. 补一条测试，证明内部代码式概念不会进入右侧报告。

验收：

- 测试中显式断言用户可见输出不包含内部动作 key 或工作流调试语义。

### CHAT-005-B：建立报告输入归一化层

文件范围：

- `analysis_projection.py`
- 可在同文件内新增小函数，若超过文件大小阈值再拆分。

要求：

1. 归一化报告字段，不直接散落在 section renderer 中取值。
2. 字段来源优先级：
   1. confirmed fields
   2. kernel context 直接字段
   3. message extracted fields
   4. user message slot extraction
   5. category prior 推断
   6. assistant message 中可识别的结构化事实
3. 推断字段需保留来源语义，不回写 confirmed fields。
4. 对办公家具类场景，允许从二级品类、交付地点、预算、交付时间推断报告展示内容。

验收：

- 同一输入下，右侧报告可填充 RFX 类型、预算、交付地点、交付时间、产品/服务、品类。
- 未确认但可推断的内容不进入 confirmed fields。

### CHAT-005-C：按模板渲染用户期望格式

文件范围：

- `analysis_content.py`

要求：

1. 保留 domain-pack 章节顺序。
2. 输出格式向 RFQ / RFX 报告模板靠齐：
   - 项目概况：表格。
   - 需求与交付范围：列表 + 子项。
   - 预算与商务条款：表格。
   - 供应商评估与决策机制：表格。
   - 项目里程碑与排期：表格。
   - 输出物与交付格式：列表。
   - 当前假设：编号列表。
   - 待补充信息 / 高价值校准：列表。
3. 对缺失字段只在必要位置标注“待确认”，不要整段充满占位。
4. 若 prompt 设置的 output contract 与 domain-pack 章节不同，优先按设置中心输出顺序与 domain-pack 章节取交集，再补 domain-pack 必要章节。

验收：

- 右侧报告截图应接近用户认可的格式：表格 + 编号章节 + 业务清单。
- 不再出现散乱的内部解释段落。

### CHAT-005-D：用户可见清洗

文件范围：

- 优先新增 `analysis_visibility.py`
- `analysis_projection.py` 在输出前调用

要求：

1. 对 `markdown`、`document.summary`、`document.sections[].content`、`next_steps[].label` 做清洗。
2. 内部 code / workflow / debug 语义不得出现在用户可见 payload。
3. 清洗规则只处理展示文本，不改变结构化真状态。
4. 清洗函数必须是纯函数，无 IO、无 provider 调用。

验收：

- 测试中注入包含内部动作 key 的 assistant message，最终 `analysis_payload` 不包含该 key。
- 对应位置替换为中文业务表达。

### CHAT-005-E：回归测试与人工验收

文件范围：

- `adapters/http_api/tests/test_chat_downstream_projection.py`
- `adapters/http_api/tests/test_analysis_content_schema_rules.py`

测试要求：

1. 非分析模式但用户明确要求 RFX / 分析报告时，右侧报告出现。
2. 右侧报告按模板章节输出。
3. 报告包含表格结构。
4. 报告包含字段推断内容。
5. 报告不包含内部代码式概念。
6. 原生 structured analysis payload 不被覆盖。

建议命令：

```bash
.venv/bin/python -m pytest adapters/http_api/tests/test_chat_downstream_projection.py adapters/http_api/tests/test_analysis_content_schema_rules.py -q
```

完成前不得标记 Done。

## 7. 排期

| 日期 | 任务 | 产出 | 验收 |
|---|---|---|---|
| 2026-05-20 | CHAT-005-A / CHAT-005-B | 投影输入审计与字段归一化 | 字段来源优先级清楚，测试覆盖内部概念不外露 |
| 2026-05-21 | CHAT-005-C | 模板化报告渲染 | 右侧报告使用表格、编号章节、业务清单 |
| 2026-05-22 | CHAT-005-D / CHAT-005-E | 用户可见清洗与回归测试 | 局部 pytest 通过，人工截图验收通过 |

## 8. 验收清单

开发完成后必须逐项确认：

- [ ] 用户右侧看到的是业务报告，不是代码或工作流调试信息。
- [ ] 报告标题、章节、表格和列表符合配置模板口径。
- [ ] 可推断字段已用于报告展示。
- [ ] 推断字段未被写入 confirmed fields。
- [ ] 原生 structured analysis payload 不被覆盖。
- [ ] 非 structured markdown payload 可被 xiaocai 投影为模板报告。
- [ ] `analysis_payload.markdown`、`document.sections[].content`、`next_steps` 都经过用户可见清洗。
- [ ] 相关 pytest 通过。

## 9. 回滚点

若上线后右侧报告异常：

1. 可先回滚 `analysis_content.py` 的模板渲染改动。
2. 保留用户可见清洗逻辑，避免内部概念泄漏。
3. 若 projection 触发过多，可收紧 `analysis_projection._should_project_analysis` 的触发条件。
4. 不回滚 FLARE 或前端，因为本任务不应修改其 authoritative runtime。
