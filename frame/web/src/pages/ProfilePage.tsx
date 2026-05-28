import ProfilePanel from '@/components/settings/ProfilePanel'
import './settings-page.css'

type ProfilePageProps = {
  onLogout?: () => void
}

const PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || 'project-default'

function ProfilePage(_props: ProfilePageProps) {
  return (
    <div className="xiaocai-settings-page settings-page settings-page--frameless">
      <main className="settings-page-main">
        <ProfilePanel projectId={PROJECT_ID} />
      </main>
    </div>
  )
}

export default ProfilePage
