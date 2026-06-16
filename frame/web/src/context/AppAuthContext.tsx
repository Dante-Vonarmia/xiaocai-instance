import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  authApi,
  clearAccessToken,
  clearCurrentUserId,
  getAccessToken,
  getCurrentUserId,
  hasSessionAuthMarker,
  projectApi,
  setAccessToken,
  setCurrentUserId,
} from '@/services/api'
import { clearCurrentUserDisplayName, setCurrentUserDisplayName } from '@/services/authSession'
import { exchangeCaigouChinaCredential } from '@/services/caigouChinaAuthApi'

const AUTH_CHANGED_EVENT = 'xiaocai-auth-change'
const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'
const MOCK_AUTH_ENABLED = import.meta.env.DEV || import.meta.env.VITE_ENABLE_MOCK_AUTH === 'true'
const CAIGOU_CHINA_CREDENTIAL_PARAMS = ['credential', 'login_ticket', 'ticket', 'token', 'sso_ticket', 'auth_code'] as const
const COOKIE_SESSION_AUTH_STATE = 'cookie-session'

type AuthStage = 'idle' | 'loading' | 'error'
type AuthMode = 'host_token' | 'wechat_code' | 'caigou_china' | 'mock'
type AuthEntryMode = 'host_token' | 'wechat_code' | 'caigou_china' | 'select'

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
  mockAuthEnabled: boolean
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
const DEFAULT_MOCK_USER = MOCK_USERS[0]

const AppAuthContext = createContext<AppAuthContextValue | null>(null)

function resolveAuthParams(): AuthParams {
  const searchParams = new URLSearchParams(window.location.search)
  const hostToken = (searchParams.get('host_token') || '').trim()
  const wechatCode = (searchParams.get('wechat_code') || '').trim()
  const credential = CAIGOU_CHINA_CREDENTIAL_PARAMS
    .map((paramName) => (searchParams.get(paramName) || '').trim())
    .find(Boolean) || ''
  if (hostToken) {
    return { mode: 'host_token', value: hostToken }
  }
  if (wechatCode) {
    return { mode: 'wechat_code', value: wechatCode }
  }
  if (credential) {
    return { mode: 'caigou_china', value: credential }
  }
  return { mode: 'select', value: '' }
}

function clearCredentialFromUrl() {
  const url = new URL(window.location.href)
  CAIGOU_CHINA_CREDENTIAL_PARAMS.forEach((paramName) => {
    url.searchParams.delete(paramName)
  })
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`)
}

function resetAuthState(setAccessTokenState: (value: string) => void, setAuthError: (value: string) => void, setAuthStage: (value: AuthStage) => void) {
  clearCurrentUserId()
  clearCurrentUserDisplayName()
  clearAccessToken()
  setAccessTokenState('')
  setAuthError('')
  setAuthStage('idle')
}

export function AppAuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessTokenState] = useState('')
  const [authStage, setAuthStage] = useState<AuthStage>('idle')
  const [authError, setAuthError] = useState('')
  const [selectedMockUserId, setSelectedMockUserId] = useState(DEFAULT_MOCK_USER.user_id)
  const authParams = useMemo(resolveAuthParams, [])
  const previousAuthModeRef = useRef<AuthEntryMode>(authParams.mode)
  const authParamAttemptRef = useRef('')
  const sessionRestoreAttemptRef = useRef(false)

  const selectedMockUser = useMemo(
    () => MOCK_USERS.find((item) => item.user_id === selectedMockUserId) || DEFAULT_MOCK_USER,
    [selectedMockUserId],
  )

  const authenticate = useCallback(async (manualMode?: AuthMode, manualValue?: string) => {
    if (!manualMode && authParams.mode === 'select' && getAccessToken().trim()) {
      return
    }
    const mode: AuthMode = manualMode || (authParams.mode === 'select' ? 'mock' : authParams.mode)
    const defaultValue = mode === 'mock' ? DEFAULT_MOCK_USER.user_id : ''
    const value = (manualValue || authParams.value || defaultValue).trim()

    setAuthStage('loading')
    setAuthError('')
    try {
      let result: Record<string, unknown>
      if (mode === 'host_token') {
        result = await authApi.exchangeTokenHost(value)
      } else if (mode === 'wechat_code') {
        result = await authApi.exchangeTokenWechat(value)
      } else if (mode === 'caigou_china') {
        result = await exchangeCaigouChinaCredential(value)
      } else {
        if (!MOCK_AUTH_ENABLED) {
          throw new Error('请从采购中国小程序进入云鹤AI服务')
        }
        result = await authApi.exchangeTokenMock(value)
      }

      const token = typeof result.access_token === 'string' ? result.access_token.trim() : ''
      const userIdFromResult = typeof result.user_id === 'string' ? result.user_id.trim() : ''
      const displayName = typeof result.display_name === 'string' ? result.display_name.trim() : ''
      const fallbackUserId = mode === 'mock' ? value : ''
      const userId = userIdFromResult || fallbackUserId
      if (!token) {
        throw new Error('认证响应缺少 access_token')
      }

      if (userId) {
        setCurrentUserId(userId)
      }
      setCurrentUserDisplayName(displayName || userId)
      setAccessToken(token)
      await projectApi.bindProject(DEFAULT_PROJECT_ID)
      if (mode === 'caigou_china') {
        clearCredentialFromUrl()
      }
      setAccessTokenState(token)
      setAuthStage('idle')
    } catch (error) {
      const message = error instanceof Error ? error.message : '认证失败'
      setAuthError(message)
      setAuthStage('error')
    }
  }, [authParams])

  useEffect(() => {
    if (previousAuthModeRef.current === authParams.mode) {
      return
    }
    previousAuthModeRef.current = authParams.mode
    resetAuthState(setAccessTokenState, setAuthError, setAuthStage)
  }, [authParams.mode])

  useEffect(() => {
    if (authParams.mode !== 'select' || !MOCK_AUTH_ENABLED) {
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
      if (!MOCK_AUTH_ENABLED && authParams.mode === 'select') {
        const currentToken = getAccessToken()
        if (currentToken.trim()) {
          setAccessTokenState(currentToken)
          return
        }
        if (!hasSessionAuthMarker()) {
          clearCurrentUserId()
          clearCurrentUserDisplayName()
          clearAccessToken()
          setAccessTokenState('')
          return
        }
        if (sessionRestoreAttemptRef.current || authStage === 'loading') {
          return
        }
        sessionRestoreAttemptRef.current = true
        setAuthStage('loading')
        void authApi.getSession()
          .then((result) => {
            const userId = typeof result.user_id === 'string' ? result.user_id.trim() : ''
            const displayName = typeof result.display_name === 'string' ? result.display_name.trim() : ''
            if (userId) {
              setCurrentUserId(userId)
            }
            setCurrentUserDisplayName(displayName || userId)
            setAccessTokenState(COOKIE_SESSION_AUTH_STATE)
            setAuthError('')
            setAuthStage('idle')
          })
          .catch((error) => {
            const message = error instanceof Error ? error.message : '认证失败'
            clearCurrentUserId()
            clearCurrentUserDisplayName()
            clearAccessToken()
            setAccessTokenState('')
            setAuthError(message)
            setAuthStage('idle')
          })
        return
      }
      if (MOCK_AUTH_ENABLED && authParams.mode === 'select' && authStage !== 'loading') {
        const currentUserId = getCurrentUserId().trim()
        const isKnownMockUser = MOCK_USERS.some((item) => item.user_id === currentUserId)
        if (currentUserId && !isKnownMockUser) {
          clearCurrentUserId()
          clearCurrentUserDisplayName()
          clearAccessToken()
          setAccessTokenState('')
          return
        }
      }
      const currentToken = getAccessToken()
      if (!currentToken.trim()) {
        clearCurrentUserId()
        clearCurrentUserDisplayName()
        setAccessTokenState('')
        return
      }
      setAccessTokenState(currentToken)
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
    if (authStage === 'loading' || authParams.mode === 'select') {
      return
    }
    const authParamKey = `${authParams.mode}:${authParams.value}`
    if (authParamAttemptRef.current === authParamKey) {
      return
    }
    authParamAttemptRef.current = authParamKey
    resetAuthState(setAccessTokenState, setAuthError, setAuthStage)
    void authenticate()
  }, [authStage, authParams, authenticate])

  useEffect(() => {
    if (!accessToken.trim() && authStage === 'idle' && authParams.mode === 'select' && MOCK_AUTH_ENABLED) {
      void authenticate('mock', DEFAULT_MOCK_USER.user_id)
    }
  }, [accessToken, authStage, authParams.mode, authenticate])

  useEffect(() => {
    if (!accessToken.trim()) {
      return
    }
    void projectApi.bindProject(DEFAULT_PROJECT_ID).catch(() => {
      const currentToken = getAccessToken()
      setAccessTokenState(currentToken || (hasSessionAuthMarker() ? COOKIE_SESSION_AUTH_STATE : ''))
    })
  }, [accessToken])

  const logout = useCallback(() => {
    resetAuthState(setAccessTokenState, setAuthError, setAuthStage)
    void authApi.logout().catch(() => undefined)
  }, [])

  const value = useMemo<AppAuthContextValue>(() => ({
    accessToken,
    authStage,
    authError,
    authParams,
    hasAccessToken: accessToken.trim().length > 0,
    mockAuthEnabled: MOCK_AUTH_ENABLED,
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
