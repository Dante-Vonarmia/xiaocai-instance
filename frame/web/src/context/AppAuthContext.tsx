import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  authApi,
  clearAccessToken,
  clearCurrentUserId,
  getAccessToken,
  getCurrentUserId,
  projectApi,
  setAccessToken,
  setCurrentUserId,
} from '@/services/api'

const AUTH_CHANGED_EVENT = 'xiaocai-auth-change'
const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'

type AuthStage = 'idle' | 'loading' | 'error'
type AuthMode = 'host_token' | 'wechat_code' | 'mock'
type AuthEntryMode = 'host_token' | 'wechat_code' | 'select'

type MockUser = {
  user_id: string
  label: string
  identity: string
  bearer_token: string
}

type AuthParams = {
  mode: AuthEntryMode
  value: string
}

type AppAuthContextValue = {
  accessToken: string
  authStage: AuthStage
  authError: string
  authParams: AuthParams
  hasAccessToken: boolean
  mockUsers: MockUser[]
  selectedMockUser: MockUser
  setSelectedMockUserId: (userId: string) => void
  authenticate: (manualMode?: AuthMode, manualValue?: string) => Promise<void>
  logout: () => void
}

const MOCK_USERS: MockUser[] = [
  { user_id: 'wx_user_alice', label: 'Alice（微信号 A）', identity: '手机号 138****1111', bearer_token: 'mock-bearer-alice' },
  { user_id: 'wx_user_bob', label: 'Bob（微信号 B）', identity: '手机号 139****2222', bearer_token: 'mock-bearer-bob' },
  { user_id: 'wx_user_cathy', label: 'Cathy（微信号 C）', identity: '手机号 137****3333', bearer_token: 'mock-bearer-cathy' },
]

const AppAuthContext = createContext<AppAuthContextValue | null>(null)

function resolveAuthParams(): AuthParams {
  const searchParams = new URLSearchParams(window.location.search)
  const hostToken = (searchParams.get('host_token') || '').trim()
  const wechatCode = (searchParams.get('wechat_code') || '').trim()
  if (hostToken) {
    return { mode: 'host_token', value: hostToken }
  }
  if (wechatCode) {
    return { mode: 'wechat_code', value: wechatCode }
  }
  return { mode: 'select', value: '' }
}

function resetAuthState(setAccessTokenState: (value: string) => void, setAuthError: (value: string) => void, setAuthStage: (value: AuthStage) => void) {
  clearAccessToken()
  clearCurrentUserId()
  setAccessTokenState('')
  setAuthError('')
  setAuthStage('idle')
}

export function AppAuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessTokenState] = useState('')
  const [authStage, setAuthStage] = useState<AuthStage>('idle')
  const [authError, setAuthError] = useState('')
  const [selectedMockUserId, setSelectedMockUserId] = useState(MOCK_USERS[0].user_id)
  const authParams = useMemo(resolveAuthParams, [])

  const selectedMockUser = useMemo(
    () => MOCK_USERS.find((item) => item.user_id === selectedMockUserId) || MOCK_USERS[0],
    [selectedMockUserId],
  )

  const authenticate = useCallback(async (manualMode?: AuthMode, manualValue?: string) => {
    if (!manualMode && authParams.mode === 'select' && getAccessToken().trim()) {
      return
    }
    const mode: AuthMode = manualMode || (authParams.mode === 'select' ? 'mock' : authParams.mode)
    const value = (manualValue || authParams.value || '').trim()

    setAuthStage('loading')
    setAuthError('')
    try {
      let result: Record<string, unknown>
      if (mode === 'host_token') {
        result = await authApi.exchangeTokenHost(value)
      } else if (mode === 'wechat_code') {
        result = await authApi.exchangeTokenWechat(value)
      } else {
        result = await authApi.exchangeTokenMock(value)
      }

      const token = typeof result.access_token === 'string' ? result.access_token.trim() : ''
      const userIdFromResult = typeof result.user_id === 'string' ? result.user_id.trim() : ''
      const fallbackUserId = mode === 'mock' ? value : ''
      const userId = userIdFromResult || fallbackUserId
      if (!token) {
        throw new Error('认证响应缺少 access_token')
      }

      if (userId) {
        setCurrentUserId(userId)
      }
      setAccessToken(token)
      await projectApi.bindProject(DEFAULT_PROJECT_ID)
      setAccessTokenState(token)
      setAuthStage('idle')
    } catch (error) {
      const message = error instanceof Error ? error.message : '认证失败'
      setAuthError(message)
      setAuthStage('error')
    }
  }, [authParams])

  useEffect(() => {
    resetAuthState(setAccessTokenState, setAuthError, setAuthStage)
  }, [authParams.mode])

  useEffect(() => {
    if (authParams.mode !== 'select') {
      return
    }
    const currentUserId = getCurrentUserId().trim()
    const isKnownMockUser = MOCK_USERS.some((item) => item.user_id === currentUserId)
    if (!currentUserId || isKnownMockUser) {
      return
    }
    resetAuthState(setAccessTokenState, setAuthError, setAuthStage)
  }, [authParams.mode])

  useEffect(() => {
    const syncToken = () => {
      if (authParams.mode === 'select' && authStage !== 'loading') {
        const currentUserId = getCurrentUserId().trim()
        const isKnownMockUser = MOCK_USERS.some((item) => item.user_id === currentUserId)
        if (currentUserId && !isKnownMockUser) {
          clearAccessToken()
          clearCurrentUserId()
          setAccessTokenState('')
          return
        }
      }
      setAccessTokenState(getAccessToken())
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key === 'access_token' || event.key === null) {
        syncToken()
      }
    }

    window.addEventListener('storage', handleStorage)
    window.addEventListener(AUTH_CHANGED_EVENT, syncToken as EventListener)
    syncToken()

    return () => {
      window.removeEventListener('storage', handleStorage)
      window.removeEventListener(AUTH_CHANGED_EVENT, syncToken as EventListener)
    }
  }, [authParams.mode, authStage])

  useEffect(() => {
    if (!accessToken.trim() && authStage !== 'loading' && authParams.mode !== 'select') {
      void authenticate()
    }
  }, [accessToken, authStage, authParams.mode, authenticate])

  useEffect(() => {
    if (!accessToken.trim()) {
      return
    }
    void projectApi.bindProject(DEFAULT_PROJECT_ID)
  }, [accessToken])

  const logout = useCallback(() => {
    resetAuthState(setAccessTokenState, setAuthError, setAuthStage)
  }, [])

  const value = useMemo<AppAuthContextValue>(() => ({
    accessToken,
    authStage,
    authError,
    authParams,
    hasAccessToken: accessToken.trim().length > 0,
    mockUsers: MOCK_USERS,
    selectedMockUser,
    setSelectedMockUserId,
    authenticate,
    logout,
  }), [accessToken, authStage, authError, authParams, selectedMockUser, authenticate, logout])

  return (
    <AppAuthContext.Provider value={value}>
      {children}
    </AppAuthContext.Provider>
  )
}

export function useAppAuth() {
  const context = useContext(AppAuthContext)
  if (!context) {
    throw new Error('useAppAuth must be used within AppAuthProvider')
  }
  return context
}
