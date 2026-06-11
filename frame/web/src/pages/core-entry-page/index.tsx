import { App as FlareChatCoreApp } from 'flare-chat-core'
import { useBranding } from '@/hooks/chat/useBranding'
import { getAccessToken, getCurrentUserId } from '@/services/api'
import './styles.css'

const FUNCTION_TYPE = import.meta.env.VITE_FLARE_CHAT_FUNCTION_TYPE || 'auto'
const DEFAULT_SESSION_TITLE = import.meta.env.VITE_FLARE_CHAT_DEFAULT_SESSION_TITLE || '新会话'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const INSTANCE_ID = import.meta.env.VITE_FLARE_CHAT_INSTANCE_ID || 'xiaocai'
const DOMAIN_PACK_DOMAIN = import.meta.env.VITE_FLARE_CHAT_DOMAIN_PACK_DOMAIN || 'xiaocai'
const DOMAIN_PACK_VERSION = import.meta.env.VITE_FLARE_CHAT_DOMAIN_PACK_VERSION || 'default'

function CoreEntryPage() {
  const branding = useBranding()
  const accessToken = getAccessToken()
  const currentUserId = getCurrentUserId() || 'anonymous-user'
  const projectSlot = branding.projectSlot
  const uiLabels = branding.uiLabels

  return (
    <div className="core-entry-page">
      <main className="core-entry-main">
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
          functionType={FUNCTION_TYPE}
          instanceId={INSTANCE_ID}
          instanceProfile={branding.instanceProfile}
          projectId=""
          productName={uiLabels.product_name}
          productTag={uiLabels.brand_tag}
          starterScenarios={branding.starterPrompts}
          uiLabels={uiLabels}
          userId={currentUserId}
        />
      </main>
    </div>
  )
}

export default CoreEntryPage
