import SystemConfigPanel from '@/components/settings/SystemConfigPanel'
import { SettingsProvider } from '@/context/SettingsContext'
import './settings-page.css'

type SettingsPageProps = {
  onLogout?: () => void
}

function SettingsPage(_props: SettingsPageProps) {
  return (
    <div className="xiaocai-settings-page settings-page settings-page--frameless">
      <main className="settings-page-main">
        <SettingsProvider>
          <SystemConfigPanel />
        </SettingsProvider>
      </main>
    </div>
  )
}

export default SettingsPage
