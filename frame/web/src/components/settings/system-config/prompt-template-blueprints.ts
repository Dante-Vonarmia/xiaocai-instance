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
    title: '智能检索边界与采购意图识别',
    stage: '智能检索',
    dataContractColumns: ['智能检索和边界设定', '初步意图识别'],
    inputFields: ['用户原始输入', '企业场景', '采购目的', '使用场景'],
    outputContract: ['是否企业采购场景', '采购目的', '使用场景', '建议下一步功能'],
    instruction: '识别用户是否处于企业采购场景；若不是，先说明边界，再给出可继续执行的企业采购方向。',
  },
  {
    key: 'deep_intent_confirmation',
    title: '深入意图识别与字段确认',
    stage: '需求梳理前置',
    dataContractColumns: ['深入意图识别', '需求梳理中的其他字段'],
    inputFields: ['采购目的', '使用场景', '一级品类', '二级品类', '交付地点'],
    outputContract: ['已确认字段', '缺失字段', '需要用户确认的问题', '可进入的下一阶段'],
    instruction: '结合品类目录和已有上下文判断缺失字段，只输出最需要确认的问题，避免重复询问已确认信息。',
  },
  {
    key: 'requirement_intake_result',
    title: '需求梳理结果生成',
    stage: '需求梳理',
    dataContractColumns: ['梳理的结果输出'],
    inputFields: ['项目名称', '采购目的', '使用场景', '预算金额', '交付地点', '交付时间', '产品/服务', '数量', '单位'],
    outputContract: ['项目概述', '需求部门信息', '细化需求表', '智能寻源引导'],
    instruction: '将已确认字段组织成结构化需求文档；缺失字段保留为空并标注待补充，不编造事实。',
  },
  {
    key: 'requirement_analysis',
    title: '需求分析与 RFX 策略模板',
    stage: '需求分析',
    dataContractColumns: ['需求分析前增加和优化的字段', '需求分析模板（RFX策略）'],
    inputFields: ['技术要求', '质量标准', '验收口径', '交付方式', '发票类型', '付款条款', '关键条款'],
    outputContract: ['项目理解', '市场现状', '成本结构', '风险分析', '采购策略', '供应商选择建议', '实施计划'],
    instruction: '基于需求完整性评估生成采购策略分析；明确哪些内容是推断，哪些需要用户确认。',
  },
  {
    key: 'sourcing_strategy',
    title: '智能寻源策略与供应商画像',
    stage: '智能寻源',
    dataContractColumns: ['智能寻源中的其他字段', '供应商清单输出', '寻源分析的模板'],
    inputFields: ['产品/服务', '供应商区域', '注册资金', '成立时长', '对标企业', '履约能力', '供应商资质'],
    outputContract: ['寻源需求分析', '供应商画像', '准入门槛', '优选指标', '供应商清单要求'],
    instruction: '将需求字段转成可执行的寻源策略；输出供应商筛选维度、标签和候选清单约束。',
  },
  {
    key: 'rfx_document_output',
    title: 'RFX 文档输出策略',
    stage: 'RFX输出',
    dataContractColumns: ['RFX文档输出'],
    inputFields: ['RFX类型', '评估项', '权重', '付款条款', '发票类型', '关键条款'],
    outputContract: ['RFI/RFQ/RFP/RFB 建议', '文件结构', '评分维度', '供应商回复要求'],
    instruction: '根据用户选择的 RFX 方式输出文件结构建议；允许用户覆盖系统推荐的 RFX 类型。',
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
