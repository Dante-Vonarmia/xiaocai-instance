import { FileTextOutlined, LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons'
import { Segmented } from 'antd'
import { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ProfilePanel from '@/components/settings/ProfilePanel'
import SystemConfigPanel from '@/components/settings/SystemConfigPanel'
import { APP_ROUTES, type SettingsSection } from '@/constants/routes'
import { SettingsProvider } from '@/context/SettingsContext'

type SettingsPageProps = {
  onLogout?: () => void
}

const FLARE_VERSION = '0.2.8'
const PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'

function toSection(value: string | undefined): SettingsSection {
  return value === 'system' ? 'system' : 'profile'
}

function SettingsPage({ onLogout }: SettingsPageProps) {
  const navigate = useNavigate()
  const params = useParams<{ section?: string }>()
  const section = toSection(params.section)

  const options = useMemo(() => ([
    { label: '个人信息', value: 'profile' },
    { label: '系统配置', value: 'system' },
  ]), [])

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
          onClick={() => navigate(APP_ROUTES.chat)}
        >
          <FileTextOutlined />
        </button>

        <button
          type="button"
          title="设置"
          style={{
            width: '52px',
            height: '52px',
            border: 'none',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
            color: '#ffffff',
            fontSize: '22px',
            lineHeight: 0,
            cursor: 'default',
            boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
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
              cursor: 'default',
              marginBottom: '8px',
              display: 'flex',
              justifyContent: 'center',
            }}
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

      <main style={{ flex: 1, minWidth: 0, padding: '20px 24px', overflowY: 'auto' }}>
        <SettingsProvider>
          <div style={{ marginBottom: 16 }}>
            <Segmented
              options={options}
              value={section}
              onChange={(value) => {
                navigate(value === 'system' ? APP_ROUTES.settingsSystem : APP_ROUTES.settingsProfile)
              }}
            />
          </div>
          {section === 'profile' ? <ProfilePanel projectId={PROJECT_ID} /> : <SystemConfigPanel />}
        </SettingsProvider>
      </main>
    </div>
  )
}

export default SettingsPage
