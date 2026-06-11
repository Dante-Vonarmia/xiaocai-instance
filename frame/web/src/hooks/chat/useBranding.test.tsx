import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useBranding } from '@/hooks/chat/useBranding'
import type { StarterPrompt } from '@/constants/chat'

type FetchResponse = {
  ok: boolean
  payload?: unknown
}

function mockFetchSequence(responses: FetchResponse[]) {
  const fetchMock = vi.fn().mockImplementation(async () => {
    const response = responses.shift() || { ok: false }
    return {
      ok: response.ok,
      json: async () => response.payload,
    }
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function mockLegacyBrandingFetch(payload: unknown) {
  return mockFetchSequence([{ ok: false }, { ok: true, payload }])
}

function mockAppProfileFetch(payload: unknown) {
  return mockFetchSequence([{ ok: true, payload }])
}

describe('useBranding', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('优先使用 xiaocai app-profile 注入模板入口与能力目录', async () => {
    const prompt: StarterPrompt = {
      key: 'office_furniture',
      label: '办公室家具采购',
      description: '300 人办公区家具需求。',
      prompt: '公司新办公室要采购办公家具。',
    }
    const fetchMock = mockAppProfileFetch({
      instanceProfile: {
        product_name: '小采',
        brand_tag: '采购助手',
        logo_text: '小采',
        logo_url: '/assets/logo-yunhe.svg',
        ui_labels: {
          empty_state_title: '欢迎来到小采',
          empty_state_description: '小采在手，采购不愁。',
          scenario_panel_title: '起步入口',
        },
      },
      starterScenarios: [prompt],
      composerModeOptions: [
        { value: 'requirement_intake', label: '需求梳理' },
        { value: 'analysis_mode', label: '需求分析' },
      ],
      capabilityCatalog: [
        { key: 'requirement_intake', label: '需求梳理', summary: '结构化采购需求。' },
      ],
      displayPolicy: {
        showUserFooter: true,
        showStarterScenarios: true,
      },
      branding: {
        colors: { primary: '#8b5cf6' },
        themeTokens: { appBg: '#ffffff' },
      },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.starterPrompts).toEqual([prompt])
    })
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/domain-packs/xiaocai/app-profile.json', { cache: 'no-store' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(result.current.displayPolicy.showStarterScenarios).toBe(true)
    expect(result.current.displayPolicy.showUserFooter).toBe(true)
    expect(result.current.composerModeOptions.map((item) => item.value)).toEqual([
      'requirement_intake',
      'analysis_mode',
    ])
    expect(result.current.capabilityCatalog.map((item) => item.key)).toEqual(['requirement_intake'])
    expect(result.current.branding.colors?.primary).toBe('#8b5cf6')
    expect(result.current.branding.themeTokens?.appBg).toBe('#ffffff')
    expect(result.current.instanceProfile.ui_labels.scenario_panel_title).toBe('起步入口')
  })

  it('没有配置 starterPrompts 时不回退默认案例', async () => {
    const fetchMock = mockLegacyBrandingFetch({
      instance: { displayName: '测试品牌' },
      ui: { chat: { uiLabels: {} } },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.uiLabels.product_name).toBe('测试品牌')
    })
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/domain-packs/xiaocai/app-profile.json', { cache: 'no-store' })
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/domain-packs/branding/instance-branding.json', { cache: 'no-store' })
    expect(result.current.starterPrompts).toEqual([])
  })

  it('保留显式配置的 starterPrompts', async () => {
    const prompt: StarterPrompt = {
      key: 'recent-context-requirement',
      label: '继续最近采购需求',
      description: '从明确配置中恢复需求入口。',
      prompt: '继续梳理最近的采购需求。',
    }
    mockLegacyBrandingFetch({
      instance: { displayName: '测试品牌' },
      ui: { chat: { uiLabels: {}, starterPrompts: [prompt] } },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.uiLabels.product_name).toBe('测试品牌')
    })
    expect(result.current.starterPrompts).toEqual([prompt])
  })

  it('将品牌 logo 与名称投影到 FLARE instanceProfile', async () => {
    mockLegacyBrandingFetch({
      instance: { displayName: '测试品牌', subtitle: '测试助手' },
      branding: {
        logo: {
          light: '/assets/test-logo.svg',
        },
      },
      ui: { chat: { uiLabels: {} } },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.instanceProfile.product_name).toBe('测试品牌')
    })
    expect(result.current.instanceProfile.brand_tag).toBe('测试助手')
    expect(result.current.instanceProfile.logo_url).toBe('/assets/test-logo.svg')
    expect(result.current.instanceProfile.ui_labels.sidebar_logo_url).toBe('/assets/test-logo.svg')
  })

  it('左侧栏支持单独注入带标题字标', async () => {
    mockLegacyBrandingFetch({
      instance: { displayName: '测试品牌', subtitle: '测试助手' },
      branding: {
        logo: {
          light: '/assets/test-logo.svg',
          sidebar: '/assets/test-wordmark.svg',
        },
      },
      ui: { chat: { uiLabels: {} } },
    })

    const { result } = renderHook(() => useBranding())

    await waitFor(() => {
      expect(result.current.instanceProfile.logo_url).toBe('/assets/test-logo.svg')
    })
    expect(result.current.instanceProfile.ui_labels.product_logo_url).toBe('/assets/test-logo.svg')
    expect(result.current.instanceProfile.ui_labels.sidebar_logo_url).toBe('/assets/test-wordmark.svg')
  })
})
