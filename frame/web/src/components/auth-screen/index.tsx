import { useCallback, useMemo, type ChangeEvent } from 'react'
import './styles.css'

type MockUser = {
  user_id: string
  label: string
  identity: string
  bearer_token: string
}

type AuthScreenProps = {
  authMode: 'host_token' | 'wechat_code' | 'caigou_china' | 'select'
  authStage: 'idle' | 'loading' | 'error'
  authError: string
  mockAuthEnabled: boolean
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
  mockAuthEnabled,
  mockUsers,
  selectedMockUser,
  onSelectMockUser,
  onSubmitMock,
  onRetry,
}: AuthScreenProps) {
  const helperText = useMemo(() => (
    authMode === 'select' && mockAuthEnabled
      ? '使用测试账号进入会话，用于内部和外部联调验证。'
      : authMode === 'select'
        ? '请从采购中国小程序进入云鹤AI服务。'
      : '正在完成成员身份接入并自动进入会话。'
  ), [authMode, mockAuthEnabled])
  const loadingHint = useMemo(() => (authStage === 'loading' ? <p>认证中...</p> : null), [authStage])
  const showMockForm = authMode === 'select' && mockAuthEnabled
  const showRetryForm = authStage === 'error' && authMode !== 'select'
  const showMockError = authStage === 'error'
  const showEntryHint = authMode === 'select' && !mockAuthEnabled
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
            <label className="auth-form__label" htmlFor="mock-user-select">测试账号</label>
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
            <button
              className="auth-form__button"
              disabled={authStage === 'loading'}
              onClick={handleSubmitMock}
              type="button"
            >
              使用测试账号进入
            </button>
            {showMockError ? <p>{authError || '认证失败，请稍后重试。'}</p> : null}
          </div>
        ) : null}
        {showEntryHint ? (
          <div className="auth-form">
            <p>请回到采购中国小程序，点击云鹤AI入口重新进入。</p>
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
