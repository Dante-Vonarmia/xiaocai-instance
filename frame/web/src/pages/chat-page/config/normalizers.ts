import {
  DEFAULT_CANVAS_UI_LABELS,
  type CanvasUiLabels,
  type StarterPrompt,
} from '@/pages/chat-page/config/constants'

export function toText(value: unknown) {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return ''
}

export function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
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
