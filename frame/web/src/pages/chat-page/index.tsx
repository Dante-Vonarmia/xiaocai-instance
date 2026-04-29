import { useInRouterContext, useNavigate } from 'react-router-dom'
import { App as FlareChatCoreApp } from 'flare-chat-core'

import { APP_ROUTES } from '@/constants/routes'
import { Shell } from '@/pages/chat-page/components/Shell'
import {
  DEFAULT_SESSION_TITLE,
  DEFAULT_FUNCTION_TYPE,
  DEFAULT_PROJECT_SLOT,
} from '@/pages/chat-page/config/constants'
import { getAccessToken, getCurrentUserId } from '@/services/api'

type ChatPageProps = {
  onLogout?: () => void
}

function ChatPage({ onLogout }: ChatPageProps) {
  const inRouterContext = useInRouterContext()
  const navigate = inRouterContext ? useNavigate() : null
  const accessToken = getAccessToken()
  const currentUserId = getCurrentUserId() || 'anonymous-user'

  return (
    <Shell
      onLogout={onLogout}
      onProfileClick={() => navigate?.(APP_ROUTES.settingsProfile)}
      workspace={(
        <FlareChatCoreApp
          apiBaseUrl={import.meta.env.VITE_API_BASE_URL || '/api'}
          apiToken={accessToken}
          backendMode="real"
          defaultProjectName={DEFAULT_PROJECT_SLOT.name}
          defaultSessionTitle={DEFAULT_SESSION_TITLE}
          functionType={DEFAULT_FUNCTION_TYPE}
          projectId={DEFAULT_PROJECT_SLOT.project_id}
          userId={currentUserId}
        />
      )}
    />
  )
}

export default ChatPage
