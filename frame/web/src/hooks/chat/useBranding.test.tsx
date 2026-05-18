import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useBranding } from '@/hooks/chat/useBranding'
import type { StarterPrompt } from '@/constants/chat'

function mockBrandingFetch(payload: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => payload,
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('useBranding', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('没有配置 starterPrompts 时不回退默认案例', async () => {
    mockBrandingFetch({
      instance: { displayName: '测试品牌' },
      ui: { chat: { uiLabels: {} } },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.uiLabels.product_name).toBe('测试品牌')
    })
    expect(result.current.starterPrompts).toEqual([])
  })

  it('保留显式配置的 starterPrompts', async () => {
    const prompt: StarterPrompt = {
      key: 'recent-context-requirement',
      label: '继续最近采购需求',
      description: '从明确配置中恢复需求入口。',
      prompt: '继续梳理最近的采购需求。',
    }
    mockBrandingFetch({
      instance: { displayName: '测试品牌' },
      ui: { chat: { uiLabels: {}, starterPrompts: [prompt] } },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.uiLabels.product_name).toBe('测试品牌')
    })
    expect(result.current.starterPrompts).toEqual([prompt])
  })
})
