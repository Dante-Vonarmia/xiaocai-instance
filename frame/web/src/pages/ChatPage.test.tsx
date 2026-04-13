import { useEffect } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ChatPage from '@/pages/ChatPage'
import { chatApi } from '@/services/api'

const streamSendSpy = vi.fn()
let streamSent = false
let streamHandlers: Record<string, unknown> = {}

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
        void streamAPI.send('test message', streamHandlers, { sessionIdOverride: 'sess-chatpage-1' })
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
    streamHandlers = {}

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
        mode: 'requirement_canvas',
        function_type: 'requirement_canvas',
      },
    })
  })

  it('将 early_patch 桥接为 next_actions payload 供 chooser 链消费', async () => {
    const onNextActions = vi.fn()
    streamHandlers = { onNextActions }

    vi.mocked(chatApi.stream).mockImplementationOnce(async (_payload, callbacks) => {
      callbacks?.onEvent?.({
        type: 'early_patch',
        data: {
          type: 'early_patch',
          question: { text: '请先确认采购类别' },
          chooser: { options: ['服务器', '网络设备'] },
          interaction_node: { id: 'category' },
          next_actions: [{ action_key: 'continue_collection', label: '继续补充' }],
          gate: { status: 'blocked', reason: 'missing_required_fields' },
          summary_confirmed: false,
        },
        raw: '',
      })
      return {
        message: '',
        cards: [],
        session_id: 'sess-chatpage-1',
        metadata: {},
      }
    })

    render(<ChatPage />)

    await waitFor(() => {
      expect(onNextActions).toHaveBeenCalledTimes(1)
    })

    const [bridged] = onNextActions.mock.calls[0] || []
    expect(bridged).toMatchObject({
      question: { text: '请先确认采购类别' },
      chooser: { options: ['服务器', '网络设备'] },
      interaction_node: { id: 'category' },
      gate: { status: 'blocked', reason: 'missing_required_fields' },
      summary_confirmed: false,
      mode_key: 'requirement_canvas',
      flow_state: 'collecting',
      collection_phase: 'collecting',
      chooser_required: true,
    })
    expect(bridged.current_question).toMatchObject({
      field_key: 'category',
      question_text: '请先确认采购类别',
    })
    expect(bridged.required_missing).toEqual(['category'])
    expect(Array.isArray(bridged.next_actions)).toBe(true)
  })
})
