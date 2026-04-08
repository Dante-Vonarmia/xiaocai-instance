import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useChat } from '@/hooks/useChat'
import { chatApi } from '@/services/api'

vi.mock('@/services/api', () => ({
  chatApi: {
    run: vi.fn(),
    stream: vi.fn(),
  },
}))

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sendMessage 成功时写入 user/assistant 消息', async () => {
    vi.mocked(chatApi.run).mockResolvedValue({
      message: 'assistant reply',
      session_id: 'sess-1',
      cards: [{ type: 'result-card', title: 'ok' }],
      metadata: {},
    })

    const { result } = renderHook(() => useChat('sess-1'))

    await act(async () => {
      await result.current.sendMessage('  hello  ')
    })

    expect(chatApi.run).toHaveBeenCalledTimes(1)
    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[0].content).toBe('hello')
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toBe('assistant reply')
    expect(result.current.messages[1].cards?.[0]).toMatchObject({ type: 'result-card' })
    expect(result.current.error).toBeNull()
  })

  it('sendMessageStream 将 chunk/card 聚合并收敛为最终结果', async () => {
    vi.mocked(chatApi.stream).mockImplementation(async (_params, callbacks = {}) => {
      callbacks.onChunk?.('hel', { type: 'token', data: {}, raw: '' })
      callbacks.onChunk?.('lo', { type: 'token', data: {}, raw: '' })
      callbacks.onCard?.({ type: 'ui_cards', cards: [{ type: 'summary', text: 'from stream' }] }, { type: 'card', data: {}, raw: '' })
      return {
        message: 'hello final',
        session_id: 'sess-2',
        cards: [],
        metadata: {},
      }
    })

    const { result } = renderHook(() => useChat('sess-2'))

    await act(async () => {
      await result.current.sendMessageStream('hello stream')
    })

    expect(chatApi.stream).toHaveBeenCalledTimes(1)
    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toBe('hello final')
    expect(result.current.messages[1].cards?.[0]).toMatchObject({ type: 'ui_cards' })
    expect(result.current.error).toBeNull()
  })

  it('sendMessageStream 失败时回写错误消息', async () => {
    vi.mocked(chatApi.stream).mockRejectedValue(new Error('network failed'))

    const { result } = renderHook(() => useChat('sess-3'))

    await act(async () => {
      await expect(result.current.sendMessageStream('will fail')).rejects.toThrow('network failed')
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toContain('发送失败：network failed')
    expect(result.current.error).toBe('network failed')
  })
})

