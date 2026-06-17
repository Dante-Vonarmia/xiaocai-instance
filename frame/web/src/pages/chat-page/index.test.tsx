import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import ChatPage from '@/pages/chat-page'
import {
  DEFAULT_FUNCTION_TYPE,
  DEFAULT_PROJECT_SLOT,
  DEFAULT_SESSION_TITLE,
} from '@/constants/chat'

const appPropsSpy = vi.fn()

vi.mock('flare-chat-core', () => ({
  App: (props: Record<string, unknown>) => {
    appPropsSpy(props)
    return <div data-testid="mock-core-app">core app</div>
  },
}))

vi.mock('@/hooks/chat/useBranding', () => ({
  useBranding: () => ({
    branding: { colors: { primary: '#8b5cf6' } },
    capabilityCatalog: [{ key: 'requirement_intake', label: '需求梳理', summary: '梳理需求' }],
    composerModeOptions: [{ value: 'requirement_intake', label: '需求梳理' }],
    displayPolicy: { showStarterScenarios: true },
    instanceProfile: {
      brand_tag: '采购助手',
      logo_text: '小采',
      logo_url: '/assets/logo-yunhe.svg',
      product_name: '小采',
      ui_labels: {
        brand_tag: '采购助手',
        canvas_empty_result: '',
        canvas_status_title: '',
        canvas_tab_result: '',
        canvas_workspace_title: '',
        empty_state_description: '',
        empty_state_title: '',
        new_session_button: '',
        product_name: '小采',
        project_title: '',
        scenario_title: '',
        session_list_title: '',
      },
    },
    interactionMode: 'auto',
    functionType: DEFAULT_FUNCTION_TYPE,
    modulePromptRegistry: [{
      module_key: 'requirement_intake',
      target_mode: 'requirement_intake',
      trigger_keywords: ['梳理'],
    }],
    projectSlot: DEFAULT_PROJECT_SLOT,
    starterPrompts: [{ key: 'training-room', label: '培训室设备采购', description: '屏幕/音频', prompt: '梳理需求' }],
    uiLabels: {
      brand_tag: '采购助手',
      canvas_empty_result: '',
      canvas_status_title: '',
      canvas_tab_result: '',
      canvas_workspace_title: '',
      empty_state_description: '',
      empty_state_title: '',
      new_session_button: '',
      product_name: '小采',
      project_title: '',
      scenario_title: '',
      session_list_title: '',
    },
  }),
}))

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api')
  return {
    ...actual,
    getAccessToken: () => 'token-test',
    getCurrentUserId: () => 'u-test',
  }
})

describe('ChatPage', () => {
  it('将 core 所需参数透传到 flare-chat-ui App', () => {
    render(<ChatPage />)

    expect(screen.getByTestId('mock-core-app')).toBeInTheDocument()
    expect(appPropsSpy).toHaveBeenCalledWith(expect.objectContaining({
      apiBaseUrl: '/api',
      apiToken: 'token-test',
      backendMode: 'real',
      defaultProjectName: DEFAULT_PROJECT_SLOT.name,
      defaultSessionTitle: DEFAULT_SESSION_TITLE,
      functionType: DEFAULT_FUNCTION_TYPE,
      modulePromptRegistry: [expect.objectContaining({
        module_key: 'requirement_intake',
        trigger_keywords: ['梳理'],
      })],
      productName: '小采',
      productTag: '采购助手',
      projectId: DEFAULT_PROJECT_SLOT.project_id,
      starterScenarios: [expect.objectContaining({ key: 'training-room' })],
      userId: 'u-test',
    }))
  })
})
