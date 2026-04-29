import { FileTextOutlined, LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons'
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { App as FlareChatCoreApp } from 'flare-chat-core'
import { APP_ROUTES } from '@/constants/routes'
import { getAccessToken, getCurrentUserId } from '@/services/api'
import { XIAOCAI_CHAT_THEME_TOKENS } from '@/theme/chatTheme'
import './styles.css'

type CoreEntryPageProps = {
  onLogout?: () => void
}

const FUNCTION_TYPE = import.meta.env.VITE_FLARE_CHAT_FUNCTION_TYPE || 'chat_component_debug'
const DEFAULT_SESSION_TITLE = import.meta.env.VITE_FLARE_CHAT_DEFAULT_SESSION_TITLE || '调试会话'
const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const FLARE_VERSION = '0.2.8'

function CoreEntryPage({ onLogout }: CoreEntryPageProps) {
  const navigate = useNavigate()
  const accessToken = getAccessToken()
  const currentUserId = getCurrentUserId() || 'anonymous-user'
  const handleGoSettings = useCallback(() => {
    navigate(APP_ROUTES.settingsProfile)
  }, [navigate])
  const logoutButton = onLogout ? (
    <button
      className="core-entry-sidebar-action"
      onClick={onLogout}
      title="退出"
      type="button"
    >
      <LogoutOutlined />
    </button>
  ) : null

  return (
    <div className="xiaocai-settings-page core-entry-page">
      <aside className="core-entry-sidebar">
        <div className="core-entry-branding">
          <div className="core-entry-branding__title">小采</div>
          <div className="core-entry-branding__subtitle">AI智能采购助手</div>
        </div>

        <div className="core-entry-sidebar-divider" />

        <button
          className="core-entry-sidebar-button core-entry-sidebar-button--active"
          type="button"
          title="返回对话"
        >
          <FileTextOutlined />
        </button>

        <button
          className="core-entry-sidebar-button core-entry-sidebar-button--neutral"
          type="button"
          title="设置"
          onClick={handleGoSettings}
        >
          <SettingOutlined />
        </button>

        <div className="core-entry-sidebar-footer">
          <div className="core-entry-sidebar-version">
            FLARE {FLARE_VERSION}
          </div>
          <button
            className="core-entry-sidebar-action"
            type="button"
            title="个人信息"
            onClick={handleGoSettings}
          >
            <UserOutlined />
          </button>
          {logoutButton}
        </div>
      </aside>

      <main className="core-entry-main">
        <FlareChatCoreApp
          apiBaseUrl={API_BASE_URL}
          apiToken={accessToken}
          backendMode="real"
          defaultSessionTitle={DEFAULT_SESSION_TITLE}
          functionType={FUNCTION_TYPE}
          projectId={DEFAULT_PROJECT_ID}
          themeTokens={XIAOCAI_CHAT_THEME_TOKENS}
          userId={currentUserId}
        />
      </main>
    </div>
  )
}

export default CoreEntryPage
