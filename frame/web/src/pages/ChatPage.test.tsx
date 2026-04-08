import { useEffect } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ChatPage from '@/pages/ChatPage'
import { chatApi } from '@/services/api'

const streamSendSpy = vi.fn()
let streamSent = false

vi.mock('@/services/backendRuntime', () => ({
  createBackendRuntime: () => ({
    sessionAPI: {},
    messageAPI: {},
  }),
}))

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api')
  return {
    ...actual,
    chatApi: {
      ...actual.chatApi,
      stream: vi.fn(),
    },
    sourceApi: {},
    getCurrentUserId: () => 'u-test',
  }
})

vi.mock('@flare/chat-ui', () => ({
  ChatWorkspace: (props: Record<string, unknown>) => {
    useEffect(() => {
      streamSendSpy(props)
      if (streamSent) {
        return
      }
      streamSent = true
      const streamAPI = props.streamAPI as {
        send?: (content: string, handlers?: Record<string, unknown>, options?: Record<string, unknown>) => Promise<unknown>
      }
      if (streamAPI?.send) {
        void streamAPI.send('test message', {}, { sessionIdOverride: 'sess-chatpage-1' })
      }
    }, [props])

    return <div data-testid="mock-chat-workspace">workspace</div>
  },
}))

describe('ChatPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    streamSendSpy.mockClear()
    streamSent = false

    vi.mocked(chatApi.stream).mockResolvedValue({
      message: 'ok',
      cards: [],
      session_id: 'sess-chatpage-1',
      metadata: {},
    })

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ ui: { chat: { starterPrompts: [] } } }),
      }),
    )
  })

  it('将 project_id/mode/function_type 透传到 chatApi.stream', async () => {
    render(<ChatPage />)

    expect(await screen.findByTestId('mock-chat-workspace')).toBeInTheDocument()

    await waitFor(() => {
      expect(chatApi.stream).toHaveBeenCalledTimes(1)
    })

    const [payload] = vi.mocked(chatApi.stream).mock.calls[0] || []
    expect(payload).toMatchObject({
      message: 'test message',
      session_id: 'sess-chatpage-1',
      context: {
        project_id: 'project-local-1',
        mode: 'auto',
        function_type: 'intelligent_sourcing',
      },
    })
  })
})
