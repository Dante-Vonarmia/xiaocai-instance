import {
  DEFAULT_CANVAS_UI_LABELS,
  type AppBranding,
  type CapabilityCatalogItem,
  type CanvasUiLabels,
  type ComposerModeOption,
  type ModulePromptRegistryItem,
  type StarterPrompt,
} from '@/constants/chat'

export function toText(value: unknown) {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return ''
}

export function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

export function toStringRecord(value: unknown): Record<string, string> {
  if (!isObject(value)) {
    return {}
  }
  return Object.fromEntries(
    Object.entries(value)
      .filter((entry): entry is [string, string] => typeof entry[1] === 'string' && entry[1].trim().length > 0),
  )
}

export function toAppBranding(value: unknown): AppBranding {
  if (!isObject(value)) {
    return {}
  }
  return {
    logo: toStringRecord(value.logo),
    colors: toStringRecord(value.colors),
    themeTokens: toStringRecord(value.themeTokens),
  }
}

export function toStarterPrompts(value: unknown): StarterPrompt[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter((item): item is StarterPrompt => (
    isObject(item)
    && typeof item.key === 'string'
    && typeof item.label === 'string'
    && typeof item.description === 'string'
    && typeof item.prompt === 'string'
  ))
}

export function toComposerModeOptions(value: unknown): ComposerModeOption[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter((item): item is ComposerModeOption => (
    isObject(item)
    && typeof item.value === 'string'
    && typeof item.label === 'string'
  ))
}

export function toCapabilityCatalog(value: unknown): CapabilityCatalogItem[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter((item): item is CapabilityCatalogItem => (
    isObject(item)
    && typeof item.key === 'string'
    && typeof item.label === 'string'
    && typeof item.summary === 'string'
  ))
}

function toOptionalStringList(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) {
    return undefined
  }
  const items = value.map(toText).filter(Boolean)
  return items.length > 0 ? items : undefined
}

function toOptionalPromptTemplates(value: unknown): Array<Record<string, unknown>> | undefined {
  if (!Array.isArray(value)) {
    return undefined
  }
  const items = value.filter(isObject)
  return items.length > 0 ? items : undefined
}

function toOptionalNumber(value: unknown): number | undefined {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : undefined
}

function isModulePromptRegistryItem(value: ModulePromptRegistryItem | null): value is ModulePromptRegistryItem {
  return Boolean(value)
}

function toModulePromptRegistryItem(value: unknown): ModulePromptRegistryItem | null {
  if (!isObject(value)) {
    return null
  }
  const moduleKey = toText(value.module_key)
  if (!moduleKey) {
    return null
  }
  return Object.fromEntries(
    Object.entries({
      module_key: moduleKey,
      label: toText(value.label) || undefined,
      target_mode: toText(value.target_mode) || undefined,
      trigger_keywords: toOptionalStringList(value.trigger_keywords),
      action_text: toText(value.action_text) || undefined,
      reason: toText(value.reason) || undefined,
      action_commands: toOptionalStringList(value.action_commands),
      target_modes: toOptionalStringList(value.target_modes),
      prompt_templates: toOptionalPromptTemplates(value.prompt_templates),
      prompt_instruction: toText(value.prompt_instruction) || undefined,
      runtime_instruction: toText(value.runtime_instruction) || undefined,
      priority: toOptionalNumber(value.priority),
    }).filter((entry) => entry[1] !== undefined),
  ) as ModulePromptRegistryItem
}

export function toModulePromptRegistry(value: unknown): ModulePromptRegistryItem[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.map(toModulePromptRegistryItem).filter(isModulePromptRegistryItem)
}

export function toCanvasUiLabels(value: unknown): CanvasUiLabels {
  if (!isObject(value)) {
    return DEFAULT_CANVAS_UI_LABELS
  }
  return {
    product_name: toText(value.product_name) || DEFAULT_CANVAS_UI_LABELS.product_name,
    brand_tag: toText(value.brand_tag) || DEFAULT_CANVAS_UI_LABELS.brand_tag,
    project_title: toText(value.project_title) || DEFAULT_CANVAS_UI_LABELS.project_title,
    session_list_title: toText(value.session_list_title) || DEFAULT_CANVAS_UI_LABELS.session_list_title,
    new_session_button: toText(value.new_session_button) || DEFAULT_CANVAS_UI_LABELS.new_session_button,
    empty_state_title: toText(value.empty_state_title) || DEFAULT_CANVAS_UI_LABELS.empty_state_title,
    empty_state_description: toText(value.empty_state_description) || DEFAULT_CANVAS_UI_LABELS.empty_state_description,
    canvas_workspace_title: toText(value.canvas_workspace_title) || DEFAULT_CANVAS_UI_LABELS.canvas_workspace_title,
    canvas_tab_result: toText(value.canvas_tab_result) || DEFAULT_CANVAS_UI_LABELS.canvas_tab_result,
    canvas_empty_result: toText(value.canvas_empty_result) || DEFAULT_CANVAS_UI_LABELS.canvas_empty_result,
    canvas_status_title: toText(value.canvas_status_title) || DEFAULT_CANVAS_UI_LABELS.canvas_status_title,
    scenario_title: toText(value.scenario_title) || DEFAULT_CANVAS_UI_LABELS.scenario_title,
  }
}
