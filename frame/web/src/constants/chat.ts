export type InteractionMode = 'auto' | 'requirement_canvas' | 'intelligent_sourcing'

export type StarterPrompt = {
  key: string
  label: string
  description: string
  prompt: string
}

export type ProjectSlot = {
  key: string
  project_id: string
  subtitle: string
  name: string
}

export type CanvasUiLabels = {
  product_name: string
  brand_tag: string
  project_title: string
  session_list_title: string
  new_session_button: string
  empty_state_title: string
  empty_state_description: string
  canvas_workspace_title: string
  canvas_tab_result: string
  canvas_empty_result: string
  canvas_status_title: string
  scenario_title: string
}

export const FLARE_VERSION = '0.2.14'
export const DEFAULT_FUNCTION_TYPE = 'auto'
export const DEFAULT_SESSION_TITLE = '新会话'
export const DEFAULT_INTERACTION_MODE: InteractionMode = 'auto'

const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'

function getDefaultProjectName(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `采购项目 ${year}-${month}-${day}`
}

export const DEFAULT_PROJECT_SLOT: ProjectSlot = {
  key: DEFAULT_PROJECT_ID,
  project_id: DEFAULT_PROJECT_ID,
  subtitle: '项目',
  name: getDefaultProjectName(),
}

export const DEFAULT_CANVAS_UI_LABELS: CanvasUiLabels = {
  product_name: '小采',
  brand_tag: '采购助手',
  project_title: '采购项目',
  session_list_title: '会话历史',
  new_session_button: '新会话',
  empty_state_title: '欢迎来到小采',
  empty_state_description: '小采在手，采购不愁。',
  canvas_workspace_title: '需求文档工作区',
  canvas_tab_result: '文档与结果',
  canvas_empty_result: '发送后在这里生成需求文档草稿，结构化结果会同步展示。',
  canvas_status_title: '文档进度',
  scenario_title: '起步入口',
}

export const DEFAULT_STARTER_PROMPTS: StarterPrompt[] = []
