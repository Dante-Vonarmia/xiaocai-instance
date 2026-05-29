import { normalizePromptTemplateDrafts, type PromptTemplateDraft } from './prompt-template-blueprints'
import {
  readCategoryTree,
  type CategoryAssetSummary,
} from './category-assets-model'
export {
  countCategoryTree,
  flattenCategoryTree,
  parseCategoryAsset,
  normalizeCategoryTreeForPayload,
  type CategoryOwnerNode,
} from './category-assets-model'

type FieldGroupKey = 'required' | 'recommended' | 'optional'

export type DomainFieldItem = {
  key: string
  label: string
  type: string
  description: string
  requiredLevel: FieldGroupKey
}

export type PromptFallbackTemplate = { key: string; text: string }

export type PromptAssetSummary = {
  askOrder: string[]
  followupTemplates: PromptFallbackTemplate[]
  analysisSections: string[]
  promptTemplates?: PromptTemplateDraft[]
}

export type DomainFieldsSummary = {
  packId: string
  version: string
  groups: Record<FieldGroupKey, DomainFieldItem[]>
}

export type DomainAssetsSummary = {
  fields: DomainFieldsSummary
  category: CategoryAssetSummary
  prompts: PromptAssetSummary
}

export type DomainAssetsDraftPayload = {
  fields: Record<FieldGroupKey, DomainFieldItem[]>
  category: Pick<CategoryAssetSummary, 'ownerNames' | 'level1Names' | 'level2Names' | 'categoryTree'>
  prompts: PromptAssetSummary
}

const FIELD_GROUPS: FieldGroupKey[] = ['required', 'recommended', 'optional']

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function hasOwn(record: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(record, key)
}

function normalizeField(value: unknown, groupKey: FieldGroupKey): DomainFieldItem {
  const record = asRecord(value)
  return {
    key: asString(record.key),
    label: asString(record.label),
    type: asString(record.type),
    description: asString(record.description),
    requiredLevel: groupKey,
  }
}

export function normalizeDomainFields(payload: unknown): DomainFieldsSummary {
  const record = asRecord(payload)
  const fieldGroups = asRecord(record.field_groups)
  const groups = FIELD_GROUPS.reduce((acc, groupKey) => {
    acc[groupKey] = asArray(fieldGroups[groupKey])
      .map((item) => normalizeField(item, groupKey))
      .filter((item) => item.key || item.label)
    return acc
  }, {} as Record<FieldGroupKey, DomainFieldItem[]>)

  return {
    packId: asString(record.pack_id) || 'xiaocai',
    version: asString(record.version) || 'default',
    groups,
  }
}

function readListBlock(text: string, blockName: string): string[] {
  const lines = text.split('\n')
  const start = lines.findIndex((line) => line.trim() === `${blockName}:`)
  if (start < 0) {
    return []
  }
  const values: string[] = []
  for (const line of lines.slice(start + 1)) {
    if (line && !line.startsWith(' ')) {
      break
    }
    const match = line.match(/^\s*-\s*(.+)$/)
    if (match) {
      values.push(match[1].trim())
    }
  }
  return values
}

function readTemplateBlock(text: string): Array<{ key: string; text: string }> {
  const lines = text.split('\n')
  const start = lines.findIndex((line) => line.trim() === 'followup_question_templates:')
  if (start < 0) {
    return []
  }
  const templates: Array<{ key: string; text: string }> = []
  for (const line of lines.slice(start + 1)) {
    if (line && !line.startsWith(' ')) {
      break
    }
    const match = line.match(/^\s{2}([^:]+):\s*["']?(.*?)["']?$/)
    if (match) {
      templates.push({ key: match[1].trim(), text: match[2].trim() })
    }
  }
  return templates
}

function readAnalysisSections(text: string): string[] {
  return text
    .split('\n')
    .filter((line) => line.startsWith('## '))
    .map((line) => line.replace(/^##\s*/, '').trim())
    .filter(Boolean)
}

export function parsePromptAssets(questionFlowText: string, analysisTemplateText: string): PromptAssetSummary {
  const workflow = parseWorkflowAsset(questionFlowText)
  if (workflow) {
    return {
      askOrder: workflow.askOrder,
      followupTemplates: workflow.followupTemplates,
      analysisSections: readAnalysisSections(analysisTemplateText),
    }
  }
  return {
    askOrder: readListBlock(questionFlowText, 'ask_order'),
    followupTemplates: readTemplateBlock(questionFlowText),
    analysisSections: readAnalysisSections(analysisTemplateText),
  }
}

function parseWorkflowAsset(text: string): Pick<PromptAssetSummary, 'askOrder' | 'followupTemplates'> | null {
  try {
    const workflow = JSON.parse(text) as Record<string, unknown>
    const blockerPolicy = asRecord(workflow.blocker_policies)
    const intakeStrategy = asRecord(workflow.intake_strategy)
    const registry = asArray(workflow.module_prompt_registry)
    const askOrder = [
      ...asArray(blockerPolicy.required_fields).map(asString),
      ...asArray(blockerPolicy.confirmation_fields).map(asString),
      ...asArray(intakeStrategy.framework_fields).map(asString),
    ].filter(Boolean)
    const followupTemplates = registry.flatMap((item) => {
      const module = asRecord(item)
      return asArray(module.prompt_templates).map((template) => {
        const record = asRecord(template)
        return {
          key: asString(record.key) || asString(module.module_key),
          text: asString(record.prompt),
        }
      })
    }).filter((item) => item.key || item.text)
    return { askOrder: Array.from(new Set(askOrder)), followupTemplates }
  } catch {
    return null
  }
}

export function countFields(fields: DomainFieldsSummary): number {
  return FIELD_GROUPS.reduce((total, key) => total + fields.groups[key].length, 0)
}

function normalizeDraftField(value: unknown, groupKey: FieldGroupKey): DomainFieldItem | null {
  const record = asRecord(value)
  const key = asString(record.key)
  const label = asString(record.label)
  if (!key && !label) {
    return null
  }
  return {
    key,
    label,
    type: asString(record.type),
    description: asString(record.description),
    requiredLevel: groupKey,
  }
}

function readStringList(value: unknown): string[] {
  return asArray(value).map(asString).filter(Boolean)
}

function readFallbackTemplates(value: unknown): PromptFallbackTemplate[] {
  return asArray(value)
    .map((item) => {
      const record = asRecord(item)
      return { key: asString(record.key), text: asString(record.text) }
    })
    .filter((item) => item.key || item.text)
}

export function buildDomainAssetsDraft(
  summary: DomainAssetsSummary,
  draftPayload?: Record<string, unknown> | null,
): DomainAssetsDraftPayload {
  const payload = asRecord(draftPayload)
  const draftFields = asRecord(payload.fields)
  const category = asRecord(payload.category)
  const prompts = asRecord(payload.prompts)
  const ownerNames = readStringList(category.ownerNames)
  const level1Names = readStringList(category.level1Names)
  const level2Names = readStringList(category.level2Names)
  const categoryTree = readCategoryTree(category.categoryTree)
  const askOrder = readStringList(prompts.askOrder)
  const followupTemplates = readFallbackTemplates(prompts.followupTemplates)
  const analysisSections = readStringList(prompts.analysisSections)
  const promptTemplates = normalizePromptTemplateDrafts(prompts.promptTemplates)
  const fields = FIELD_GROUPS.reduce((acc, groupKey) => {
    const draftItems = asArray(draftFields[groupKey])
      .map((item) => normalizeDraftField(item, groupKey))
      .filter((item): item is DomainFieldItem => Boolean(item))
    acc[groupKey] = draftItems.length ? draftItems : summary.fields.groups[groupKey]
    return acc
  }, {} as Record<FieldGroupKey, DomainFieldItem[]>)

  return {
    fields,
    category: {
      ownerNames: hasOwn(category, 'ownerNames') ? ownerNames : summary.category.ownerNames,
      level1Names: hasOwn(category, 'level1Names') ? level1Names : summary.category.level1Names,
      level2Names: hasOwn(category, 'level2Names') ? level2Names : summary.category.level2Names,
      categoryTree: hasOwn(category, 'categoryTree') ? categoryTree : summary.category.categoryTree,
    },
    prompts: {
      askOrder: hasOwn(prompts, 'askOrder') ? askOrder : summary.prompts.askOrder,
      followupTemplates: hasOwn(prompts, 'followupTemplates')
        ? followupTemplates
        : summary.prompts.followupTemplates,
      analysisSections: hasOwn(prompts, 'analysisSections')
        ? analysisSections
        : summary.prompts.analysisSections,
      promptTemplates: hasOwn(prompts, 'promptTemplates')
        ? promptTemplates
        : normalizePromptTemplateDrafts(summary.prompts.promptTemplates),
    },
  }
}

export function countDraftFields(payload: DomainAssetsDraftPayload): number {
  return FIELD_GROUPS.reduce((total, key) => total + payload.fields[key].length, 0)
}

export { FIELD_GROUPS }
