import { FileTextOutlined, LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons'
import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import ProfilePanel from '@/components/settings/ProfilePanel'
import { APP_ROUTES } from '@/constants/routes'
import './settings-page.css'

type ProfilePageProps = {
  onLogout?: () => void
}

const FLARE_VERSION = '0.2.14'
const PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'

function ProfilePage({ onLogout }: ProfilePageProps) {
  const navigate = useNavigate()
  const handleGoChat = useCallback(() => {
    navigate(APP_ROUTES.chat)
  }, [navigate])
  const handleGoSettings = useCallback(() => {
    navigate(APP_ROUTES.settingsSystem)
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
          className="settings-page-sidebar-button settings-page-sidebar-button--neutral"
          type="button"
          title="设置"
          onClick={handleGoSettings}
        >
          <SettingOutlined />
        </button>

        <div className="settings-page-sidebar-footer">
          <div className="settings-page-sidebar-version">
            小采 {FLARE_VERSION}
          </div>
          <button
            className="settings-page-sidebar-action settings-page-sidebar-action--active"
            type="button"
            title="个人信息"
          >
            <UserOutlined />
          </button>
          {logoutButton}
        </div>
      </aside>

      <main className="settings-page-main">
        <ProfilePanel projectId={PROJECT_ID} />
      </main>
    </div>
  )
}

export default ProfilePage
