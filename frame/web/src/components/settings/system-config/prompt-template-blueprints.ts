export type PromptTemplateDraft = {
  key: string
  title: string
  stage: string
  dataContractColumns: string[]
  inputFields: string[]
  outputContract: string[]
  instruction: string
}

export const DEFAULT_PROMPT_TEMPLATES: PromptTemplateDraft[] = [
  {
    key: 'intent_boundary',
    title: '采购场景准入与意图分层识别',
    stage: '智能检索',
    dataContractColumns: ['智能检索和边界设定', '初步意图识别'],
    inputFields: ['用户原始输入', '企业场景', '采购目的', '使用场景'],
    outputContract: ['场景准入结论', '采购目标摘要', '使用场景归类', '推荐承接链路'],
    instruction: '依据企业采购场景、采购目的与使用场景完成准入判定；输出采购意图层级、适用边界、推荐承接链路和需要补充的关键上下文。',
  },
  {
    key: 'deep_intent_confirmation',
    title: '需求梳理准入与关键字段确认',
    stage: '需求梳理前置',
    dataContractColumns: ['深入意图识别', '需求梳理中的其他字段'],
    inputFields: ['采购目的', '使用场景', '一级品类', '二级品类', '交付地点'],
    outputContract: ['已确认字段快照', '关键缺口清单', '当前确认事项', '阶段流转建议'],
    instruction: '基于品类目录、字段优先级和已有上下文评估需求梳理准入状态；仅针对阻塞字段生成确认事项，并同步输出已确认字段快照与阶段流转建议。',
  },
  {
    key: 'requirement_intake_result',
    title: '结构化需求基线沉淀',
    stage: '需求梳理',
    dataContractColumns: ['梳理的结果输出'],
    inputFields: ['项目名称', '采购目的', '使用场景', '预算金额', '交付地点', '交付时间', '产品/服务', '数量', '单位'],
    outputContract: ['需求基线摘要', '字段完整性状态', '待补录事项', '后续阶段建议'],
    instruction: '将已确认字段沉淀为可版本化的结构化需求基线；保留字段来源、缺口状态和待补录事项，为需求分析、寻源和 RFX 策略提供可追溯输入。',
  },
  {
    key: 'requirement_analysis',
    title: '需求分析与 RFX 策略研判',
    stage: '需求分析',
    dataContractColumns: ['需求分析前增加和优化的字段', '需求分析模板（RFX策略）'],
    inputFields: ['技术要求', '质量标准', '验收口径', '交付方式', '发票类型', '付款条款', '关键条款'],
    outputContract: ['需求理解', '市场与成本研判', '风险与约束', '采购策略', '供应商策略', '实施路径'],
    instruction: '基于字段完整性、品类属性和约束条件生成采购策略分析；区分事实字段、合理推断和待确认项，输出可供业务决策和 RFX 编制复用的结构化章节。',
  },
  {
    key: 'sourcing_strategy',
    title: '寻源策略与供应商画像框架',
    stage: '智能寻源',
    dataContractColumns: ['智能寻源中的其他字段', '供应商清单输出', '寻源分析的模板'],
    inputFields: ['产品/服务', '供应商区域', '注册资金', '成立时长', '对标企业', '履约能力', '供应商资质'],
    outputContract: ['寻源目标', '供应商画像', '准入门槛', '评估维度', '候选清单口径'],
    instruction: '将结构化需求转换为可执行的寻源策略；定义供应商画像、准入门槛、评估维度、数据来源约束和候选清单输出口径。',
  },
  {
    key: 'rfx_document_output',
    title: 'RFX 文件策略与输出控制',
    stage: 'RFX输出',
    dataContractColumns: ['RFX文档输出'],
    inputFields: ['RFX类型', '评估项', '权重', '付款条款', '发票类型', '关键条款'],
    outputContract: ['RFX 类型建议', '文件结构', '评分模型', '供应商响应要求'],
    instruction: '依据采购方式、评估项、权重和关键条款形成 RFI/RFQ/RFP/RFB 文件策略；输出文件结构、变量绑定、评分模型和供应商响应要求。',
  },
]

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(asString).filter(Boolean) : []
}

export function normalizePromptTemplateDrafts(value: unknown): PromptTemplateDraft[] {
  if (!Array.isArray(value) || value.length === 0) {
    return DEFAULT_PROMPT_TEMPLATES
  }
  const normalized = value.map((item, index) => {
    const record = asRecord(item)
    const fallback = DEFAULT_PROMPT_TEMPLATES[index]
    return {
      key: asString(record.key) || fallback?.key || `prompt_template_${index + 1}`,
      title: asString(record.title) || fallback?.title || 'Prompt 模板',
      stage: asString(record.stage) || fallback?.stage || '配置中心',
      dataContractColumns: asStringList(record.dataContractColumns).length
        ? asStringList(record.dataContractColumns)
        : fallback?.dataContractColumns || [],
      inputFields: asStringList(record.inputFields),
      outputContract: asStringList(record.outputContract),
      instruction: asString(record.instruction) || fallback?.instruction || '',
    }
  })
  return normalized.filter((item) => item.key && item.title)
}
