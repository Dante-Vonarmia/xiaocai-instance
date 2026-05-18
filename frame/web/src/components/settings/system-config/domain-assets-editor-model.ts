import {
  FIELD_GROUPS,
  type DomainAssetsDraftPayload,
  type DomainFieldItem,
  type PromptFallbackTemplate,
} from './domain-assets-model'
import { normalizePromptTemplateDrafts, type PromptTemplateDraft } from './prompt-template-blueprints'

export const FIELD_GROUP_LABELS = {
  required: '必填字段',
  recommended: '建议字段',
  optional: '可选字段',
}

export type EditorState = {
  fields: DomainAssetsDraftPayload['fields']
  ownerNames: string[]
  level1Names: string[]
  askOrder: string[]
  followupTemplates: PromptFallbackTemplate[]
  analysisSections: string[]
  promptTemplates: PromptTemplateDraft[]
}

export function hydrateEditorState(payload: DomainAssetsDraftPayload): EditorState {
  return {
    fields: FIELD_GROUPS.reduce((acc, key) => {
      acc[key] = payload.fields[key]
      return acc
    }, {} as EditorState['fields']),
    ownerNames: payload.category.ownerNames,
    level1Names: payload.category.level1Names,
    askOrder: payload.prompts.askOrder,
    followupTemplates: payload.prompts.followupTemplates,
    analysisSections: payload.prompts.analysisSections,
    promptTemplates: normalizePromptTemplateDrafts(payload.prompts.promptTemplates),
  }
}

export function buildPayload(state: EditorState): DomainAssetsDraftPayload {
  return {
    fields: FIELD_GROUPS.reduce((acc, key) => {
      acc[key] = state.fields[key].filter((field) => field.key || field.label)
      return acc
    }, {} as DomainAssetsDraftPayload['fields']),
    category: {
      ownerNames: state.ownerNames.map((item) => item.trim()).filter(Boolean),
      level1Names: state.level1Names.map((item) => item.trim()).filter(Boolean),
    },
    prompts: {
      askOrder: state.askOrder.map((item) => item.trim()).filter(Boolean),
      followupTemplates: state.followupTemplates.filter((item) => item.key || item.text),
      analysisSections: state.analysisSections.map((item) => item.trim()).filter(Boolean),
      promptTemplates: state.promptTemplates,
    },
  }
}

export function emptyField(requiredLevel: DomainFieldItem['requiredLevel']): DomainFieldItem {
  return { key: '', label: '', type: 'string', description: '', requiredLevel }
}
