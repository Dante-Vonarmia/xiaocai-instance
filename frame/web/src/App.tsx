import { useCallback, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import {
  authApi,
  clearAccessToken,
  clearCurrentUserId,
  getAccessToken,
  projectApi,
  setAccessToken,
  setCurrentUserId,
} from './services/api'

const AUTH_CHANGED_EVENT = 'xiaocai-auth-change'
const DEFAULT_PROJECT_ID = 'project-local-1'
type AuthStage = 'idle' | 'loading' | 'error'
type AuthMode = 'host_token' | 'wechat_code' | 'mock'
type AuthEntryMode = 'host_token' | 'wechat_code' | 'select'

const MOCK_USERS = [
  {
    user_id: 'wx_user_alice',
    label: 'Alice（微信号 A）',
    identity: '手机号 138****1111',
    bearer_token: 'mock-bearer-alice',
  },
  {
    user_id: 'wx_user_bob',
    label: 'Bob（微信号 B）',
    identity: '手机号 139****2222',
    bearer_token: 'mock-bearer-bob',
  },
  {
    user_id: 'wx_user_cathy',
    label: 'Cathy（微信号 C）',
    identity: '手机号 137****3333',
    bearer_token: 'mock-bearer-cathy',
  },
]

function App() {
  const [accessToken, setAccessTokenState] = useState(() => {
    const searchParams = new URLSearchParams(window.location.search)
    const hasExternalAuthParam = Boolean(
      (searchParams.get('host_token') || '').trim()
      || (searchParams.get('wechat_code') || '').trim(),
    )
    if (hasExternalAuthParam) {
      return ''
    }
    return getAccessToken()
  })
  const [authStage, setAuthStage] = useState<AuthStage>('idle')
  const [authError, setAuthError] = useState('')
  const [selectedMockUserId, setSelectedMockUserId] = useState(MOCK_USERS[0].user_id)

  const authParams = useMemo(() => {
    const searchParams = new URLSearchParams(window.location.search)
    const hostToken = (searchParams.get('host_token') || '').trim()
    const wechatCode = (searchParams.get('wechat_code') || '').trim()

    if (hostToken) {
      return { mode: 'host_token' as AuthEntryMode, value: hostToken }
    }

    if (wechatCode) {
      return { mode: 'wechat_code' as AuthEntryMode, value: wechatCode }
    }

    return { mode: 'select' as AuthEntryMode, value: '' }
  }, [])
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

      setAccessToken(token)
      if (userId) {
        setCurrentUserId(userId)
      }
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
    if (authParams.mode === 'select') {
      return
    }
    clearAccessToken()
    clearCurrentUserId()
    setAccessTokenState('')
    setAuthError('')
    setAuthStage('idle')
  }, [authParams.mode])

  useEffect(() => {
    if (authParams.mode !== 'select') {
      return
    }

    clearAccessToken()
    clearCurrentUserId()
    setAccessTokenState('')
    setAuthError('')
    setAuthStage('idle')
  }, [authParams.mode])

  useEffect(() => {
    const syncToken = () => {
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
  }, [])
  
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

  const handleLogout = () => {
    clearAccessToken()
    clearCurrentUserId()
    setAccessTokenState('')
    setAuthError('')
    setAuthStage('idle')
  }

  const hasAccessToken = accessToken.trim().length > 0

  return (
    <BrowserRouter>
      {hasAccessToken ? (
        <Routes>
          <Route path="/" element={<ChatPage onLogout={handleLogout} />} />
          <Route path="*" element={<ChatPage onLogout={handleLogout} />} />
        </Routes>
      ) : (
        <main className="auth-screen">
          <section className="auth-card">
            <div className="auth-card__eyebrow">xiaocai frame web</div>
            <h1>进入采购助手</h1>
            <p>
              {authParams.mode === 'select'
                ? '选择模拟身份后进入会话，不同用户会看到自己的会话历史。'
                : '正在完成成员身份接入并自动进入会话。'}
            </p>
            {authStage === 'loading' ? (
              <p>认证中...</p>
            ) : null}
            {authParams.mode === 'select' ? (
              <div className="auth-form">
                <label className="auth-form__label" htmlFor="mock-user-select">模拟用户</label>
                <select
                  className="auth-form__input"
                  disabled={authStage === 'loading'}
                  id="mock-user-select"
                  onChange={(event) => setSelectedMockUserId(event.target.value)}
                  value={selectedMockUser.user_id}
                >
                  {MOCK_USERS.map((item) => (
                    <option key={item.user_id} value={item.user_id}>
                      {item.label}
                    </option>
                  ))}
                </select>
                <p>身份：{selectedMockUser.identity}</p>
                <p>Bearer Token：{selectedMockUser.bearer_token}</p>
                <button
                  className="auth-form__button"
                  disabled={authStage === 'loading'}
                  onClick={() => void authenticate('mock', selectedMockUser.user_id)}
                  type="button"
                >
                  进入会话
                </button>
                {authStage === 'error' ? <p>{authError || '认证失败，请稍后重试。'}</p> : null}
              </div>
            ) : null}
            {authStage === 'error' && authParams.mode !== 'select' ? (
              <div className="auth-form">
                <p>{authError || '认证失败，请稍后重试。'}</p>
                <button className="auth-form__button" onClick={() => void authenticate()} type="button">
                  重试
                </button>
              </div>
            ) : null}
          </section>
        </main>
      )}
    </BrowserRouter>
  )
}

export default App
