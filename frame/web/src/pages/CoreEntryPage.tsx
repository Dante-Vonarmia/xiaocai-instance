import { FileTextOutlined, LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { APP_ROUTES } from '@/constants/routes'

type CoreEntryPageProps = {
  onLogout?: () => void
}

const CORE_ENTRY_URL = import.meta.env.VITE_FLARE_CORE_ENTRY_URL || '/core/'
const FLARE_VERSION = '0.2.4'

function CoreEntryPage({ onLogout }: CoreEntryPageProps) {
  const navigate = useNavigate()

  return (
    <div className="xiaocai-settings-page" style={{ height: '100vh', display: 'flex', background: '#f6f8fc' }}>
      <aside
        style={{
          width: '80px',
          minWidth: '80px',
          borderRight: '1px solid #e5e7eb',
          background: '#ffffff',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
          padding: '24px 14px',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', marginBottom: '8px' }}>
          <div style={{ fontSize: '18px', fontWeight: 600, color: '#1f2937', lineHeight: 1.3 }}>小采</div>
          <div style={{ marginTop: '4px', fontSize: '11px', color: '#8c8c8c', lineHeight: 1.3 }}>AI智能采购助手</div>
        </div>

        <div style={{ width: '40px', height: '1px', background: 'rgba(0, 0, 0, 0.06)', margin: '8px 0' }} />

        <button
          type="button"
          title="返回对话"
          style={{
            width: '52px',
            height: '52px',
            border: 'none',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#ffffff',
            fontSize: '22px',
            lineHeight: 0,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)',
          }}
        >
          <FileTextOutlined />
        </button>

        <button
          type="button"
          title="设置"
          style={{
            width: '52px',
            height: '52px',
            border: '1px solid #d1d5db',
            borderRadius: '14px',
            background: '#ffffff',
            color: '#6b7280',
            fontSize: '22px',
            lineHeight: 0,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onClick={() => navigate(APP_ROUTES.settingsProfile)}
        >
          <SettingOutlined />
        </button>

        <div style={{ marginTop: 'auto', width: '100%' }}>
          <div style={{ fontSize: '11px', color: '#9ca3af', textAlign: 'center', marginBottom: '8px' }}>
            FLARE {FLARE_VERSION}
          </div>
          <button
            type="button"
            title="个人信息"
            style={{
              width: '100%',
              border: '1px solid #d1d5db',
              background: '#ffffff',
              borderRadius: '8px',
              padding: '8px 0',
              fontSize: '16px',
              color: '#6b7280',
              cursor: 'pointer',
              marginBottom: '8px',
              display: 'flex',
              justifyContent: 'center',
            }}
            onClick={() => navigate(APP_ROUTES.settingsProfile)}
          >
            <UserOutlined />
          </button>
          {onLogout ? (
            <button
              onClick={onLogout}
              title="退出"
              style={{
                width: '100%',
                border: '1px solid #d1d5db',
                background: '#ffffff',
                borderRadius: '8px',
                padding: '8px 0',
                fontSize: '16px',
                color: '#6b7280',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'center',
              }}
              type="button"
            >
              <LogoutOutlined />
            </button>
          ) : null}
        </div>
      </aside>

      <main style={{ flex: 1, minWidth: 0 }}>
        <iframe
          src={CORE_ENTRY_URL}
          title="flare-chat-core-entry"
          style={{ border: 'none', width: '100%', height: '100%' }}
        />
      </main>
    </div>
  )
}

export default CoreEntryPage
