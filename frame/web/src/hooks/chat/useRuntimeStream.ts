import { useCallback, useReducer, useRef } from 'react'

import { chatApi } from '@/services/api'
import type { BackendRuntime } from '@/services/backendRuntime'
import { DEFAULT_FUNCTION_TYPE, DEFAULT_SESSION_TITLE, type InteractionMode } from '@/constants/chat'
import { toText } from '@/hooks/chat/normalizers'

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

type StreamState = {
  loading: boolean
  error: { message: string; type: string } | null
}

type StreamAction =
  | { type: 'request_start' }
  | { type: 'request_end' }
  | { type: 'request_error'; payload: { message: string; type: string } }

const INITIAL_STREAM_STATE: StreamState = {
  loading: false,
  error: null,
}

function streamReducer(state: StreamState, action: StreamAction): StreamState {
  if (action.type === 'request_start') {
    return { loading: true, error: null }
  }
  if (action.type === 'request_end') {
    return { ...state, loading: false }
  }
  if (action.type === 'request_error') {
    return { loading: false, error: action.payload }
  }
  return state
}

function dispatchStreamEvent(
  eventType: string,
  payload: unknown,
  handlers: StreamHandlers,
) {
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
  if (eventType === 'next_actions' || eventType === 'early_patch' || eventType === 'final_patch') {
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
    return nested.some((item) => hasUsefulCardContent(item))
  }

  const hasTextField = ['title', 'description', 'summary', 'reason', 'message', 'label']
    .some((key) => typeof card[key] === 'string' && card[key].trim())
  if (hasTextField) {
    return true
  }

  const hasListField = ['items', 'options', 'candidates', 'sources', 'references', 'actions']
    .some((key) => Array.isArray(card[key]) && card[key].length > 0)
  if (hasListField) {
    return true
  }

  return ['payload', 'data', 'fields']
    .some((key) => {
      const value = card[key]
      return Boolean(
        value
        && typeof value === 'object'
        && !Array.isArray(value)
        && Object.keys(value as Record<string, unknown>).length > 0
      )
    })
}

function toUiCards(payload: Record<string, unknown> | null | undefined) {
  if (!payload || typeof payload !== 'object') {
    return [] as Record<string, unknown>[]
  }
  if (typeof payload.type !== 'string' || payload.type.trim().toLowerCase() !== 'ui_cards') {
    return [] as Record<string, unknown>[]
  }
  if (!Array.isArray(payload.cards)) {
    return [] as Record<string, unknown>[]
  }
  return payload.cards
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
    .filter((item) => hasUsefulCardContent(item))
}

export function useRuntimeStream(runtime: BackendRuntime, projectId: string, interactionMode: InteractionMode) {
  const [state, dispatch] = useReducer(streamReducer, INITIAL_STREAM_STATE)
  const abortControllerRef = useRef<AbortController | null>(null)
  const lastSessionIdRef = useRef('')
  const lastRequestRef = useRef<{ content: string; handlers: StreamHandlers; options: StreamOptions } | null>(null)

  const send = useCallback(async (content: string, handlers: StreamHandlers = {}, options: StreamOptions = {}) => {
    const trimmedContent = toText(content)
    if (!trimmedContent) {
      return
    }

    let sessionId = toText(options.sessionIdOverride) || toText(lastSessionIdRef.current)
    if (!sessionId) {
      try {
        const created = await runtime.sessionAPI.create({
          function_type: DEFAULT_FUNCTION_TYPE,
          title: DEFAULT_SESSION_TITLE,
          project_id: projectId,
        })
        sessionId = toText(created?.sessionId)
      } catch (error) {
        const message = error instanceof Error ? error.message : '会话创建失败，请重试'
        dispatch({ type: 'request_error', payload: { message, type: 'api' } })
        handlers.onError?.({ message })
        return
      }
    }
    if (!sessionId) {
      const message = '会话未就绪，无法发送，请刷新后重试'
      dispatch({ type: 'request_error', payload: { message, type: 'api' } })
      handlers.onError?.({ message })
      return
    }

    lastSessionIdRef.current = sessionId
    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller
    lastRequestRef.current = { content: trimmedContent, handlers, options }
    dispatch({ type: 'request_start' })
    handlers.onAgentStatus?.({ agent: 'xiaocai-api', status: 'running', label: '请求中' })

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
            enabled_capabilities: Array.isArray(options.enabledCapabilities) ? options.enabledCapabilities : [],
          },
        },
        {
          signal: controller.signal,
          onEvent: (event) => {
            const eventType = typeof event.type === 'string' ? event.type.trim().toLowerCase() : ''
            dispatchStreamEvent(eventType, event.data, handlers)
          },
          onChunk: (chunk) => {
            streamedContent += chunk
            handlers.onContent?.(chunk)
          },
          onCard: (card) => {
            const nextCards = toUiCards(card)
            if (nextCards.length > 0) {
              handlers.onUICards?.({ cards: nextCards })
            }
          },
        onError: (apiError) => {
          const message = apiError.message || '发送失败'
          dispatch({ type: 'request_error', payload: { message, type: 'api' } })
          handlers.onError?.({ message })
        },
      },
      )

      if (toText(response.session_id)) {
        lastSessionIdRef.current = toText(response.session_id)
      }
      const finalCards = response.cards
        .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
        .filter((item) => hasUsefulCardContent(item))
      if (finalCards.length > 0) {
        handlers.onUICards?.({ cards: finalCards })
      }

      handlers.onAgentStatus?.({ agent: 'xiaocai-api', status: 'completed', label: '完成' })
      const finalContent = toText(response.message) || streamedContent
      handlers.onComplete?.(finalContent)
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      throw error
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
      dispatch({ type: 'request_end' })
    }
  }, [interactionMode, projectId, runtime])

  const retry = useCallback(async () => {
    const request = lastRequestRef.current
    if (request) {
      await send(request.content, request.handlers, request.options)
    }
  }, [send])

  const abort = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    dispatch({ type: 'request_end' })
  }, [])

  return { send, retry, abort, loading: state.loading, error: state.error }
}
