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

export const FLARE_VERSION = '0.2.8'
export const DEFAULT_FUNCTION_TYPE = 'auto'
export const DEFAULT_SESSION_TITLE = '新会话'
export const DEFAULT_INTERACTION_MODE: InteractionMode = 'auto'

const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'

export const DEFAULT_PROJECT_SLOT: ProjectSlot = {
  key: DEFAULT_PROJECT_ID,
  project_id: DEFAULT_PROJECT_ID,
  subtitle: '项目',
  name: '采购项目',
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

export const DEFAULT_STARTER_PROMPTS: StarterPrompt[] = [
  {
    key: 'starter-test-server',
    label: '我要采购一批测试服务器',
    description: '需求梳理：先补齐预算、用途、配置和交付约束。',
    prompt: '我要采购一批测试服务器，请先帮我梳理采购需求并列出还缺的关键信息。',
  },
  {
    key: 'starter-gpu-requirement',
    label: '帮我梳理 GPU 采购需求',
    description: '参数检索与对比：明确显卡型号、显存、功耗、兼容性。',
    prompt: '帮我梳理 GPU 采购需求，按参数检索与对比视角列出必填项和对比维度。',
  },
  {
    key: 'starter-analysis-generation',
    label: '根据资料生成需求分析',
    description: '需求分析生成：沉淀目标、范围、风险与验收要点。',
    prompt: '根据我已有资料生成一版采购需求分析，包含目标、范围、关键参数、风险和验收建议。',
  },
  {
    key: 'starter-procurement-direction',
    label: '给我一个采购建议方向',
    description: '供应商寻源（按需启用）：在需求明确后进入候选筛选。',
    prompt: '给我一个采购建议方向：先判断我的需求成熟度，再给出下一步行动建议。',
  },
]
