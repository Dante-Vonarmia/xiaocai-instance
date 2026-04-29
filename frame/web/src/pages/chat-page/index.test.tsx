import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import ChatPage from '@/pages/chat-page'
import {
  DEFAULT_FUNCTION_TYPE,
  DEFAULT_PROJECT_SLOT,
  DEFAULT_SESSION_TITLE,
} from '@/constants/chat'

const appPropsSpy = vi.fn()

vi.mock('flare-chat-ui', () => ({
  App: (props: Record<string, unknown>) => {
    appPropsSpy(props)
    return <div data-testid="mock-core-app">core app</div>
  },
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
      projectId: DEFAULT_PROJECT_SLOT.project_id,
      userId: 'u-test',
    }))
  })
})
