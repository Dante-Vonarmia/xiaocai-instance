import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ConfigProvider } from 'antd'
import { FileTextOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { ChatWorkspace } from '@flare/chat-ui'
import { chatApi, getCurrentUserId, sourceApi } from '@/services/api'
import { createBackendRuntime, type BackendRuntime } from '@/services/backendRuntime'

type ChatPageProps = {
  onLogout?: () => void
}

const FLARE_VERSION = '0.2.0'

type StreamHandlers = {
  onAgentStatus?: (payload: unknown) => void
  onThinkingTrace?: (payload: { trace: unknown }) => void
  onExecutionTrace?: (payload: unknown) => void
  onContent?: (chunk: string) => void
  onWorkspaceActivation?: (payload: unknown) => void
  onUICards?: (payload: { cards: Record<string, unknown>[] }) => void
  onFieldProgress?: (payload: unknown) => void
  onRequirementDraft?: (payload: unknown) => void
  onNextActions?: (payload: unknown) => void
  onSourcingCandidates?: (payload: unknown) => void
  onRiskSummary?: (payload: unknown) => void
  onShortlistUpdated?: (payload: unknown) => void
  onEvaluationReportReady?: (payload: unknown) => void
  onDoc?: (payload: { doc: unknown }) => void
  onInstanceProfile?: (payload: unknown) => void
  onComplete?: (finalContent: string) => void
  onError?: (payload: { message: string }) => void
}

type StreamOptions = {
  sessionIdOverride?: string
  enabledCapabilities?: string[]
}

type Runtime = BackendRuntime
type InteractionMode = 'auto' | 'intelligent_sourcing'
type StarterPrompt = {
  key: string
  label: string
  description: string
  prompt: string
}

const DEFAULT_FUNCTION_TYPE = 'intelligent_sourcing'
const DEFAULT_SESSION_TITLE = '新会话'
const DEFAULT_INTERACTION_MODE: InteractionMode = 'auto'
const DEFAULT_PROJECT_SLOT = {
  key: 'project-local-1',
  project_id: 'project-local-1',
  subtitle: '项目',
  name: '本地演示项目',
}
const CANVAS_UI_LABELS = {
  product_name: '小采',
  brand_tag: '采购助手',
  project_title: '采购项目',
  session_list_title: '会话历史',
  new_session_button: '新会话',
  empty_state_title: '欢迎来到小采',
  empty_state_description: '小采在手，采购不愁。',
  canvas_workspace_title: '需求文档工作区',
  canvas_tab_result: '文档与结果',
  canvas_empty_result: '发送后在这里生成需求文档草稿，结构化结果会同步展示。',
  canvas_status_title: '文档进度',
  scenario_title: '起步入口',
} as const

const DEFAULT_STARTER_PROMPTS: StarterPrompt[] = [
  {
    key: 'starter-test-server',
    label: '我要采购一批测试服务器',
    description: '需求梳理：先补齐预算、用途、配置和交付约束。',
    prompt: '我要采购一批测试服务器，请先帮我梳理采购需求并列出还缺的关键信息。',
  },
  {
    key: 'starter-gpu-requirement',
    label: '帮我梳理 GPU 采购需求',
    description: '参数检索与对比：明确显卡型号、显存、功耗、兼容性。',
    prompt: '帮我梳理 GPU 采购需求，按参数检索与对比视角列出必填项和对比维度。',
  },
  {
    key: 'starter-analysis-generation',
    label: '根据资料生成需求分析',
    description: '需求分析生成：沉淀目标、范围、风险与验收要点。',
    prompt: '根据我已有资料生成一版采购需求分析，包含目标、范围、关键参数、风险和验收建议。',
  },
  {
    key: 'starter-procurement-direction',
    label: '给我一个采购建议方向',
    description: '供应商寻源（按需启用）：在需求明确后进入候选筛选。',
    prompt: '给我一个采购建议方向：先判断我的需求成熟度，再给出下一步行动建议。',
  },
]
function toText(value: unknown) {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return ''
}

function toUiCards(payload: Record<string, unknown> | null | undefined) {
  if (!payload || typeof payload !== 'object') {
    return [] as Record<string, unknown>[]
  }
  const eventType = typeof payload.type === 'string' ? payload.type.trim().toLowerCase() : ''
  if (eventType !== 'ui_cards') {
    return [] as Record<string, unknown>[]
  }
  const candidate = payload.cards
  if (!Array.isArray(candidate)) {
    return [] as Record<string, unknown>[]
  }
  return candidate
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
    .filter((item) => hasUsefulCardContent(item))
}

function hasUsefulCardContent(card: Record<string, unknown>): boolean {
  const cardType = typeof card.type === 'string' ? card.type.trim().toLowerCase() : ''
  if (!cardType) {
    return false
  }

  if (cardType === 'ui_cards' || cardType === 'cards') {
    const nested = Array.isArray(card.cards)
      ? card.cards.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
      : []
    return nested.some((item): boolean => hasUsefulCardContent(item))
  }

  const textFields = ['title', 'description', 'summary', 'reason', 'message', 'label']
  for (const key of textFields) {
    const value = card[key]
    if (typeof value === 'string' && value.trim()) {
      return true
    }
  }

  const arrayFields = ['items', 'options', 'candidates', 'sources', 'references', 'actions']
  for (const key of arrayFields) {
    const value = card[key]
    if (Array.isArray(value) && value.length > 0) {
      return true
    }
  }

  const objectFields = ['payload', 'data', 'fields']
  for (const key of objectFields) {
    const value = card[key]
    if (value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value as Record<string, unknown>).length > 0) {
      return true
    }
  }

  return false
}

function useRuntimeStream(runtime: Runtime, projectId: string, interactionMode: InteractionMode) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{ message: string; type: string } | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const lastRequestRef = useRef<{
    content: string
    handlers: StreamHandlers
    options: StreamOptions
  } | null>(null)

  const send = useCallback(async (
    content: string,
    handlers: StreamHandlers = {},
    options: StreamOptions = {},
  ) => {
    const sessionId = toText(options.sessionIdOverride)
    const trimmedContent = toText(content)

    if (!sessionId || !trimmedContent) {
      return
    }

    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller
    lastRequestRef.current = { content: trimmedContent, handlers, options }

    setLoading(true)
    setError(null)
    handlers.onAgentStatus?.({
      agent: 'xiaocai-api',
      status: 'running',
      label: '请求中',
    })

    let streamedContent = ''

    try {
      const response = await chatApi.stream(
        {
          message: trimmedContent,
          session_id: sessionId,
          context: {
            project_id: projectId,
            function_type: DEFAULT_FUNCTION_TYPE,
            mode: interactionMode,
            enabled_capabilities: Array.isArray(options.enabledCapabilities)
              ? options.enabledCapabilities
              : [],
          },
        },
        {
          signal: controller.signal,
          onEvent: (event) => {
            const eventType = typeof event.type === 'string' ? event.type.trim().toLowerCase() : ''
            const payload = event.data

            if (eventType === 'thinking_trace') {
              handlers.onThinkingTrace?.({ trace: payload })
              return
            }
            if (eventType === 'execution_trace') {
              handlers.onExecutionTrace?.(payload)
              return
            }
            if (eventType === 'workspace_activation') {
              handlers.onWorkspaceActivation?.(payload)
              return
            }
            if (eventType === 'field_progress') {
              handlers.onFieldProgress?.(payload)
              return
            }
            if (eventType === 'requirement_draft') {
              handlers.onRequirementDraft?.(payload)
              return
            }
            if (eventType === 'next_actions') {
              handlers.onNextActions?.(payload)
              return
            }
            if (eventType === 'sourcing_candidates') {
              handlers.onSourcingCandidates?.(payload)
              return
            }
            if (eventType === 'risk_summary') {
              handlers.onRiskSummary?.(payload)
              return
            }
            if (eventType === 'shortlist_updated') {
              handlers.onShortlistUpdated?.(payload)
              return
            }
            if (eventType === 'evaluation_report_ready') {
              handlers.onEvaluationReportReady?.(payload)
              return
            }
            if (eventType === 'doc') {
              handlers.onDoc?.({ doc: payload })
              return
            }
            if (eventType === 'instance_profile') {
              handlers.onInstanceProfile?.(payload)
            }
          },
          onChunk: (chunk) => {
            streamedContent += chunk
            handlers.onContent?.(chunk)
          },
          onCard: (card) => {
            const nextCards = toUiCards(card)
            if (nextCards.length === 0) {
              return
            }
            handlers.onUICards?.({ cards: nextCards })
          },
        },
      )

      const finalContent = toText(response.message) || streamedContent
      const finalCards = response.cards
        .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
        .filter((item) => hasUsefulCardContent(item))

      if (finalCards.length > 0) {
        handlers.onUICards?.({ cards: finalCards })
      }

      handlers.onAgentStatus?.({
        agent: 'xiaocai-api',
        status: 'completed',
        label: '完成',
      })
      handlers.onComplete?.(finalContent)
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }

      const message = error instanceof Error ? error.message : '发送失败'
      setError({ message, type: 'api' })
      handlers.onError?.({ message })
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }

      setLoading(false)
    }
  }, [runtime, projectId, interactionMode])

  const retry = useCallback(async () => {
    const request = lastRequestRef.current
    if (!request) {
      return
    }

    await send(request.content, request.handlers, request.options)
  }, [send])

  const abort = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    setLoading(false)
  }, [])

  return {
    send,
    retry,
    abort,
    loading,
    error,
  }
}

function ChatPage({ onLogout }: ChatPageProps) {
  const runtime = useMemo(
    () => createBackendRuntime(),
    [],
  )
  const interactionMode: InteractionMode = DEFAULT_INTERACTION_MODE
  const [starterPrompts, setStarterPrompts] = useState<StarterPrompt[]>([])
  const projectSlot = useMemo(() => ({ ...DEFAULT_PROJECT_SLOT }), [])
  const streamAPI = useRuntimeStream(runtime, projectSlot.project_id, interactionMode)
  const projectItems = useMemo(() => [projectSlot], [projectSlot])
  const currentUserId = useMemo(() => getCurrentUserId() || 'anonymous-user', [])

  useEffect(() => {
    let cancelled = false
    const loadStarterPrompts = async () => {
      try {
        const response = await fetch('/domain-pack/branding/instance-branding.json', { cache: 'no-store' })
        if (!response.ok || cancelled) {
          return
        }
        const payload = await response.json() as {
          ui?: {
            chat?: {
              starterPrompts?: unknown[]
            }
          }
        }
        const candidate = payload.ui?.chat?.starterPrompts
        if (!Array.isArray(candidate) || cancelled) {
          setStarterPrompts(DEFAULT_STARTER_PROMPTS)
          return
        }
        const next = candidate.filter((item): item is StarterPrompt => (
          Boolean(item)
          && typeof item === 'object'
          && typeof (item as { key?: unknown }).key === 'string'
          && typeof (item as { label?: unknown }).label === 'string'
          && typeof (item as { description?: unknown }).description === 'string'
          && typeof (item as { prompt?: unknown }).prompt === 'string'
        ))
        setStarterPrompts(next.length > 0 ? next : DEFAULT_STARTER_PROMPTS)
      } catch {
        if (!cancelled) {
          setStarterPrompts(DEFAULT_STARTER_PROMPTS)
        }
      }
    }
    void loadStarterPrompts()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="xiaocai-chat-page" style={{ height: '100vh', display: 'flex', background: '#f6f8fc' }}>
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
          title="需求管理助手"
          style={{
            width: '52px',
            height: '52px',
            border: 'none',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#ffffff',
            fontSize: '22px',
            lineHeight: 0,
            cursor: 'default',
            boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: 'translateY(-2px)',
          }}
        >
          <FileTextOutlined />
        </button>
        <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#667eea', marginTop: '-8px' }} />

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

      <div style={{ display: 'flex', flex: 1, flexDirection: 'column', minWidth: 0, minHeight: 0 }}>
        <div style={{ flex: 1, minHeight: 0 }}>
          <ConfigProvider
            theme={{
              token: {
                borderRadius: 10,
              },
            }}
          >
            <ChatWorkspace
              composerPlaceholder="请输入采购需求"
              defaultTitle={DEFAULT_SESSION_TITLE}
              functionType={DEFAULT_FUNCTION_TYPE}
              identityContext={{
                project_id: projectSlot.project_id,
                user_id: currentUserId,
              }}
              messageAPI={runtime.messageAPI}
              onProjectSelect={() => undefined}
              projectItems={projectItems}
              projectSlot={projectSlot}
              sourceAPI={sourceApi}
              starterPrompts={starterPrompts}
              sessionAPI={runtime.sessionAPI}
              sessionListTitle="会话列表"
              streamAPI={streamAPI}
              uiLabels={CANVAS_UI_LABELS}
            />
          </ConfigProvider>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
