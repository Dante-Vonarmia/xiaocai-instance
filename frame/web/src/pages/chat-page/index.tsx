import { useCallback, useMemo } from 'react'
import { useInRouterContext, useNavigate } from 'react-router-dom'
import { App as FlareChatCoreApp } from 'flare-chat-ui'

import { APP_ROUTES } from '@/constants/routes'
import { DEFAULT_FUNCTION_TYPE, DEFAULT_PROJECT_SLOT, DEFAULT_SESSION_TITLE } from '@/constants/chat'
import { Shell } from '@/components/chat/Shell'
import { getAccessToken, getCurrentUserId } from '@/services/api'

type ChatPageProps = {
  onLogout?: () => void
}

function ChatPage({ onLogout }: ChatPageProps) {
  const inRouterContext = useInRouterContext()
  const navigate = inRouterContext ? useNavigate() : null
  const accessToken = getAccessToken()
  const currentUserId = getCurrentUserId() || 'anonymous-user'
  const handleProfileClick = useCallback(() => {
    navigate?.(APP_ROUTES.settingsProfile)
  }, [navigate])
  const workspace = useMemo(() => (
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
  ), [accessToken, currentUserId])

  return (
    <Shell
      onLogout={onLogout}
      onProfileClick={handleProfileClick}
      workspace={workspace}
    />
  )
}

export default ChatPage
