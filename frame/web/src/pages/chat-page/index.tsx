import { useMemo } from 'react'
import { App as FlareChatCoreApp } from 'flare-chat-core'

import { DEFAULT_FUNCTION_TYPE, DEFAULT_PROJECT_SLOT, DEFAULT_SESSION_TITLE } from '@/constants/chat'
import { Shell } from '@/components/chat/Shell'
import { getAccessToken, getCurrentUserId } from '@/services/api'

type ChatPageProps = {
  onLogout?: () => void
}

function ChatPageView() {
  const accessToken = getAccessToken()
  const currentUserId = getCurrentUserId() || 'anonymous-user'
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

  return <Shell workspace={workspace} />
}

function ChatPage(_props: ChatPageProps) {
  return <ChatPageView />
}

export default ChatPage
