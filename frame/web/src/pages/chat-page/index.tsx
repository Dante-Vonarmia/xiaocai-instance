import { useMemo } from 'react'
import { App as FlareChatCoreApp } from 'flare-chat-core'

import { DEFAULT_FUNCTION_TYPE, DEFAULT_PROJECT_SLOT, DEFAULT_SESSION_TITLE } from '@/constants/chat'
import { Shell } from '@/components/chat/Shell'
import { useBranding } from '@/hooks/chat/useBranding'
import { getAccessToken, getCurrentUserId } from '@/services/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const INSTANCE_ID = import.meta.env.VITE_FLARE_CHAT_INSTANCE_ID || 'xiaocai'
const DOMAIN_PACK_DOMAIN = import.meta.env.VITE_FLARE_CHAT_DOMAIN_PACK_DOMAIN || 'xiaocai'
const DOMAIN_PACK_VERSION = import.meta.env.VITE_FLARE_CHAT_DOMAIN_PACK_VERSION || 'default'

function ChatPageView() {
  const branding = useBranding()
  const accessToken = getAccessToken()
  const currentUserId = getCurrentUserId() || 'anonymous-user'
  const projectSlot = branding.projectSlot || DEFAULT_PROJECT_SLOT
  const uiLabels = branding.uiLabels

  /**
   * Keep the core app mounted through one stable workspace node while still
   * forwarding app-profile contracts that drive tips and capability entries.
   */
  const workspace = useMemo(() => (
    <FlareChatCoreApp
      apiBaseUrl={API_BASE_URL}
      apiToken={accessToken}
      backendMode="real"
      branding={branding.branding}
      capabilityCatalog={branding.capabilityCatalog}
      composerModeOptions={branding.composerModeOptions}
      defaultProjectName={projectSlot.name}
      defaultSessionTitle={DEFAULT_SESSION_TITLE}
      displayPolicy={branding.displayPolicy}
      domainPackDomain={DOMAIN_PACK_DOMAIN}
      domainPackVersion={DOMAIN_PACK_VERSION}
      functionType={DEFAULT_FUNCTION_TYPE}
      instanceId={INSTANCE_ID}
      instanceProfile={branding.instanceProfile}
      modulePromptRegistry={branding.modulePromptRegistry}
      productName={uiLabels.product_name}
      productTag={uiLabels.brand_tag}
      projectId={projectSlot.project_id}
      starterScenarios={branding.starterPrompts}
      uiLabels={uiLabels}
      userId={currentUserId}
    />
  ), [accessToken, branding, currentUserId, projectSlot, uiLabels])

  return <Shell workspace={workspace} />
}

function ChatPage() {
  return <ChatPageView />
}

export default ChatPage
