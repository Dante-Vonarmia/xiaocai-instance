import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AppAuthProvider, useAppAuth } from '@/context/AppAuthContext'

const apiMocks = vi.hoisted(() => ({
  bindProject: vi.fn(),
  clearAccessToken: vi.fn(),
  clearCurrentUserId: vi.fn(),
  exchangeCaigouChinaCredential: vi.fn(),
  exchangeTokenHost: vi.fn(),
  exchangeTokenMock: vi.fn(),
  exchangeTokenWechat: vi.fn(),
  getAccessToken: vi.fn(),
  getCurrentUserId: vi.fn(),
  getSession: vi.fn(),
  hasSessionAuthMarker: vi.fn(),
  logout: vi.fn(),
  setAccessToken: vi.fn(),
  setCurrentUserId: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  authApi: {
    exchangeTokenHost: apiMocks.exchangeTokenHost,
    exchangeTokenMock: apiMocks.exchangeTokenMock,
    exchangeTokenWechat: apiMocks.exchangeTokenWechat,
    getSession: apiMocks.getSession,
    logout: apiMocks.logout,
  },
  clearAccessToken: apiMocks.clearAccessToken,
  clearCurrentUserId: apiMocks.clearCurrentUserId,
  getAccessToken: apiMocks.getAccessToken,
  getCurrentUserId: apiMocks.getCurrentUserId,
  hasSessionAuthMarker: apiMocks.hasSessionAuthMarker,
  projectApi: {
    bindProject: apiMocks.bindProject,
  },
  setAccessToken: apiMocks.setAccessToken,
  setCurrentUserId: apiMocks.setCurrentUserId,
}))

vi.mock('@/services/caigouChinaAuthApi', () => ({
  exchangeCaigouChinaCredential: apiMocks.exchangeCaigouChinaCredential,
}))

function AuthProbe() {
  const { hasAccessToken } = useAppAuth()
  return <div>{hasAccessToken ? 'authed' : 'blocked'}</div>
}

describe('AppAuthProvider caigou china login', () => {
  let storedToken = ''
  let storedUserId = ''

  beforeEach(() => {
    cleanup()
    vi.clearAllMocks()
    storedToken = ''
    storedUserId = ''
    apiMocks.getAccessToken.mockImplementation(() => storedToken)
    apiMocks.getCurrentUserId.mockImplementation(() => storedUserId)
    apiMocks.setAccessToken.mockImplementation((token: string) => {
      storedToken = token
    })
    apiMocks.setCurrentUserId.mockImplementation((userId: string) => {
      storedUserId = userId
    })
    apiMocks.clearAccessToken.mockImplementation(() => {
      storedToken = ''
    })
    apiMocks.clearCurrentUserId.mockImplementation(() => {
      storedUserId = ''
    })
    apiMocks.bindProject.mockResolvedValue({})
    apiMocks.getSession.mockResolvedValue({})
    apiMocks.hasSessionAuthMarker.mockReturnValue(false)
    apiMocks.logout.mockResolvedValue({})
    window.localStorage.clear()
    window.sessionStorage.clear()
    window.history.replaceState({}, '', '/')
  })

  it('exchanges credential and clears credential query from URL', async () => {
    apiMocks.exchangeCaigouChinaCredential.mockResolvedValue({
      access_token: 'xiaocai-token',
      user_id: '316',
      display_name: '韩经伟',
    })
    window.history.replaceState({}, '', '/?credential=credential-123')

    render(
      <AppAuthProvider>
        <AuthProbe />
      </AppAuthProvider>,
    )

    await waitFor(() => expect(apiMocks.exchangeCaigouChinaCredential).toHaveBeenCalledWith('credential-123'))
    await waitFor(() => expect(screen.getByText('authed')).toBeInTheDocument())
    expect(apiMocks.setAccessToken).toHaveBeenCalledWith('xiaocai-token')
    expect(apiMocks.setCurrentUserId).toHaveBeenCalledWith('316')
    expect(window.sessionStorage.getItem('current_user_display_name')).toBe('韩经伟')
    expect(window.location.search).toBe('')
  })

  it('exchanges ticket alias and clears all credential aliases from URL', async () => {
    apiMocks.exchangeCaigouChinaCredential.mockResolvedValue({
      access_token: 'xiaocai-token',
      user_id: '316',
      display_name: '采购会员',
    })
    window.history.replaceState({}, '', '/?ticket=ticket-alias&token=stale-token')

    render(
      <AppAuthProvider>
        <AuthProbe />
      </AppAuthProvider>,
    )

    await waitFor(() => expect(apiMocks.exchangeCaigouChinaCredential).toHaveBeenCalledWith('ticket-alias'))
    await waitFor(() => expect(screen.getByText('authed')).toBeInTheDocument())
    expect(window.sessionStorage.getItem('current_user_display_name')).toBe('采购会员')
    expect(window.location.search).toBe('')
  })

  it('exchanges credential even when a previous token exists', async () => {
    storedToken = 'old-token'
    storedUserId = 'old-user'
    apiMocks.exchangeCaigouChinaCredential.mockResolvedValue({
      access_token: 'new-token',
      user_id: '316',
    })
    window.history.replaceState({}, '', '/?credential=credential-456')

    render(
      <AppAuthProvider>
        <AuthProbe />
      </AppAuthProvider>,
    )

    await waitFor(() => expect(apiMocks.exchangeCaigouChinaCredential).toHaveBeenCalledWith('credential-456'))
    expect(apiMocks.clearAccessToken).toHaveBeenCalled()
    expect(apiMocks.setAccessToken).toHaveBeenCalledWith('new-token')
    expect(apiMocks.setCurrentUserId).toHaveBeenCalledWith('316')
  })
})
