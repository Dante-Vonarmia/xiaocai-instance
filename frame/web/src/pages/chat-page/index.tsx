import { useCallback, useEffect, useMemo, useState } from 'react'
import { useInRouterContext, useNavigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { ChatWorkspace } from '@flare/chat-ui'

import { APP_ROUTES } from '@/constants/routes'
import { Shell } from '@/pages/chat-page/components/Shell'
import {
  DEFAULT_INTERACTION_MODE,
  DEFAULT_SESSION_TITLE,
  type InteractionMode,
} from '@/pages/chat-page/config/constants'
import { useBranding } from '@/pages/chat-page/hooks/useBranding'
import { useRuntimeStream } from '@/pages/chat-page/hooks/useRuntimeStream'
import { getCurrentUserId } from '@/services/api'
import { createBackendRuntime } from '@/services/backendRuntime'
import { instanceSourceApi } from '@/services/instanceApi'
import { XIAOCAI_CHAT_ANTD_THEME, XIAOCAI_CHAT_THEME_TOKENS } from '@/theme/chatTheme'

type ChatPageProps = {
  onLogout?: () => void
}

function ChatPage({ onLogout }: ChatPageProps) {
  const inRouterContext = useInRouterContext()
  const navigate = inRouterContext ? useNavigate() : null
  const runtime = useMemo(() => createBackendRuntime(), [])
  const branding = useBranding()
  const [interactionMode, setInteractionMode] = useState<InteractionMode>(DEFAULT_INTERACTION_MODE)

  /**
   * Keep local mode state aligned with branding defaults.
   *
   * This page owns the current UI mode, but the initial/default mode still comes
   * from instance branding. Syncing here prevents the page from drifting when the
   * branding payload is loaded or refreshed after mount.
   */
  useEffect(() => {
    setInteractionMode(branding.interactionMode)
  }, [branding.interactionMode])

  /**
   * Stable stream wiring for ChatWorkspace.
   *
   * Keep runtime stream assembly outside JSX so the workspace receives a single,
   * explicit runtime boundary instead of ad-hoc render-time composition.
   */
  const streamAPI = useRuntimeStream(runtime, branding.projectSlot.project_id, interactionMode)
  const projectItems = useMemo(() => [branding.projectSlot], [branding.projectSlot])
  const currentUserId = useMemo(() => getCurrentUserId() || 'anonymous-user', [])

  /**
   * Stable identity payload passed into ChatWorkspace.
   *
   * This object participates in child props comparison/effects, so it must not be
   * recreated inline during every render.
   */
  const identityContext = useMemo(() => ({
    project_id: branding.projectSlot.project_id,
    user_id: currentUserId,
  }), [branding.projectSlot.project_id, currentUserId])
  /**
   * Stable mode-change bridge for ChatWorkspace.
   *
   * Keep event handlers out of JSX so render output stays declarative and child
   * components do not observe a brand-new callback on every render.
   */
  const handleModeChange = useCallback((nextModeKey: string) => {
    const normalized = String(nextModeKey || '').trim() as InteractionMode
    if (normalized) {
      setInteractionMode(normalized)
    }
  }, [])

  return (
    <Shell
      onLogout={onLogout}
      onProfileClick={() => navigate?.(APP_ROUTES.settingsProfile)}
      workspace={(
        <ConfigProvider theme={XIAOCAI_CHAT_ANTD_THEME}>
          <ChatWorkspace
            themeTokens={XIAOCAI_CHAT_THEME_TOKENS}
            activeModeKey={interactionMode}
            composerPlaceholder="请输入采购需求"
            defaultTitle={DEFAULT_SESSION_TITLE}
            functionType={branding.functionType}
            identityContext={identityContext}
            messageAPI={runtime.messageAPI}
            onModeChange={handleModeChange}
            onProjectSelect={() => undefined}
            projectItems={projectItems}
            projectSlot={branding.projectSlot}
            sessionAPI={runtime.sessionAPI}
            sessionListTitle="会话列表"
            sourceAPI={instanceSourceApi}
            starterPrompts={branding.starterPrompts}
            streamAPI={streamAPI}
            uiLabels={branding.uiLabels}
          />
        </ConfigProvider>
      )}
    />
  )
}

export default ChatPage
