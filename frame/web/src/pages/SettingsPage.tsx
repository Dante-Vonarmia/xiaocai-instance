import { FileTextOutlined, LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons'
import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import SystemConfigPanel from '@/components/settings/SystemConfigPanel'
import { APP_ROUTES } from '@/constants/routes'
import { SettingsProvider } from '@/context/SettingsContext'
import './settings-page.css'

type SettingsPageProps = {
  onLogout?: () => void
}

const FLARE_VERSION = '0.2.16'

function SettingsPage({ onLogout }: SettingsPageProps) {
  const navigate = useNavigate()
  const handleGoChat = useCallback(() => {
    navigate(APP_ROUTES.chat)
  }, [navigate])
  const handleGoProfile = useCallback(() => {
    navigate(APP_ROUTES.profile)
  }, [navigate])
  const logoutButton = useMemo(() => (
    onLogout ? (
      <button
        className="settings-page-sidebar-action"
        onClick={onLogout}
        title="退出"
        type="button"
      >
        <LogoutOutlined />
      </button>
    ) : null
  ), [onLogout])

  return (
    <div className="xiaocai-settings-page settings-page">
      <aside className="settings-page-sidebar">
        <div className="settings-page-branding">
          <div className="settings-page-branding__title">小采</div>
          <div className="settings-page-branding__subtitle">AI智能采购助手</div>
        </div>

        <div className="settings-page-divider" />

        <button
          className="settings-page-sidebar-button settings-page-sidebar-button--neutral"
          type="button"
          title="返回对话"
          onClick={handleGoChat}
        >
          <FileTextOutlined />
        </button>

        <button
          className="settings-page-sidebar-button settings-page-sidebar-button--active"
          type="button"
          title="设置"
        >
          <SettingOutlined />
        </button>

        <div className="settings-page-sidebar-footer">
          <div className="settings-page-sidebar-version">
            小采 {FLARE_VERSION}
          </div>
          <button
            className="settings-page-sidebar-action"
            type="button"
            title="个人信息"
            onClick={handleGoProfile}
          >
            <UserOutlined />
          </button>
          {logoutButton}
        </div>
      </aside>

      <main className="settings-page-main">
        <SettingsProvider>
          <SystemConfigPanel />
        </SettingsProvider>
      </main>
    </div>
  )
}

export default SettingsPage
