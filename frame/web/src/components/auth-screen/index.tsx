import { useCallback, useMemo, type ChangeEvent } from 'react'
import './styles.css'

type MockUser = {
  user_id: string
  label: string
  identity: string
  bearer_token: string
}

type AuthScreenProps = {
  authMode: 'host_token' | 'wechat_code' | 'select'
  authStage: 'idle' | 'loading' | 'error'
  authError: string
  mockUsers: MockUser[]
  selectedMockUser: MockUser
  onSelectMockUser: (userId: string) => void
  onSubmitMock: (userId: string) => void
  onRetry: () => void
}

export function AuthScreen({
  authMode,
  authStage,
  authError,
  mockUsers,
  selectedMockUser,
  onSelectMockUser,
  onSubmitMock,
  onRetry,
}: AuthScreenProps) {
  const helperText = useMemo(() => (
    authMode === 'select'
      ? '选择模拟身份后进入会话，不同用户会看到自己的会话历史。'
      : '正在完成成员身份接入并自动进入会话。'
  ), [authMode])
  const loadingHint = useMemo(() => (authStage === 'loading' ? <p>认证中...</p> : null), [authStage])
  const showMockForm = authMode === 'select'
  const showRetryForm = authStage === 'error' && authMode !== 'select'
  const showMockError = authStage === 'error'
  const handleMockUserChange = useCallback((event: ChangeEvent<HTMLSelectElement>) => {
    onSelectMockUser(event.target.value)
  }, [onSelectMockUser])
  const handleSubmitMock = useCallback(() => {
    onSubmitMock(selectedMockUser.user_id)
  }, [onSubmitMock, selectedMockUser.user_id])

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <div className="auth-card__eyebrow">xiaocai frame web</div>
        <h1>进入采购助手</h1>
        <p>{helperText}</p>
        {loadingHint}
        {showMockForm ? (
          <div className="auth-form">
            <label className="auth-form__label" htmlFor="mock-user-select">模拟用户</label>
            <select
              className="auth-form__input"
              disabled={authStage === 'loading'}
              id="mock-user-select"
              onChange={handleMockUserChange}
              value={selectedMockUser.user_id}
            >
              {mockUsers.map((item) => (
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
              onClick={handleSubmitMock}
              type="button"
            >
              进入会话
            </button>
            {showMockError ? <p>{authError || '认证失败，请稍后重试。'}</p> : null}
          </div>
        ) : null}
        {showRetryForm ? (
          <div className="auth-form">
            <p>{authError || '认证失败，请稍后重试。'}</p>
            <button className="auth-form__button" onClick={onRetry} type="button">
              重试
            </button>
          </div>
        ) : null}
      </section>
    </main>
  )
}
