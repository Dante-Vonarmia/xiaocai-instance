import { useCallback, useRef, useState } from 'react'

import { chatApi } from '@/services/api'
import type { BackendRuntime } from '@/services/backendRuntime'
import { DEFAULT_FUNCTION_TYPE, DEFAULT_SESSION_TITLE, type InteractionMode } from '@/pages/chat-page/config/constants'
import { toText } from '@/pages/chat-page/config/normalizers'

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

function toOptionText(option: unknown) {
  if (typeof option === 'string' && option.trim()) {
    return option.trim()
  }
  if (option && typeof option === 'object') {
    const candidate = option as Record<string, unknown>
    const value = candidate.label ?? candidate.text ?? candidate.value
    if (typeof value === 'string' && value.trim()) {
      return value.trim()
    }
  }
  return ''
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

  for (const key of ['title', 'description', 'summary', 'reason', 'message', 'label']) {
    if (typeof card[key] === 'string' && card[key].trim()) {
      return true
    }
  }
  for (const key of ['items', 'options', 'candidates', 'sources', 'references', 'actions']) {
    if (Array.isArray(card[key]) && card[key].length > 0) {
      return true
    }
  }
  for (const key of ['payload', 'data', 'fields']) {
    const value = card[key]
    if (value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value as Record<string, unknown>).length > 0) {
      return true
    }
  }
  return false
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

function toPendingPatchPayload(payload: unknown) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return null
  }
  const source = payload as Record<string, unknown>
  const question = source.question && typeof source.question === 'object' && !Array.isArray(source.question)
    ? source.question as Record<string, unknown>
    : null
  const chooser = source.chooser && typeof source.chooser === 'object' && !Array.isArray(source.chooser)
    ? source.chooser as Record<string, unknown>
    : null
  const interactionNode = source.interaction_node && typeof source.interaction_node === 'object' && !Array.isArray(source.interaction_node)
    ? source.interaction_node as Record<string, unknown>
    : null
  const gate = source.gate && typeof source.gate === 'object' && !Array.isArray(source.gate)
    ? source.gate as Record<string, unknown>
    : null
  const commandType = toText(source.command_type).toLowerCase()
  const gateStatus = toText(gate?.status).toLowerCase()
  const hasPendingSignal = Boolean(question || chooser || interactionNode)
    || commandType === 'continue_collection'
    || gateStatus === 'blocked'
    || gateStatus === 'collecting'
    || gateStatus === 'pending'
  if (!hasPendingSignal) {
    return null
  }

  const fieldKey = toText(question?.field_key ?? chooser?.field_key ?? interactionNode?.field_key ?? interactionNode?.id ?? 'pending')
  const optionSource = Array.isArray(question?.options)
    ? question.options
    : (Array.isArray(chooser?.options) ? chooser.options : [])
  const nextActions = Array.isArray(source.next_actions)
    ? source.next_actions
    : (Array.isArray(source.actions)
      ? source.actions
      : [{ action_key: 'continue_collection', label: '继续补充', status: 'available', target_mode: 'requirement_canvas' }])

  return {
    ...source,
    mode_key: toText(source.mode_key) || 'requirement_canvas',
    flow_state: toText(source.flow_state) || (source.summary_confirmed === true ? 'completed' : 'collecting'),
    collection_phase: toText(source.collection_phase) || (source.summary_confirmed === true ? 'completed' : 'collecting'),
    current_question: (
      source.current_question
      && typeof source.current_question === 'object'
      && !Array.isArray(source.current_question)
    )
      ? source.current_question
      : {
        field_key: fieldKey,
        field_label: toText(question?.field_label) || fieldKey,
        question_text: toText(question?.question_text ?? question?.text ?? chooser?.question_text ?? interactionNode?.title ?? interactionNode?.text ?? '请补充当前问题'),
        options: optionSource.map((item) => toOptionText(item)).filter(Boolean),
        step_index: Number(question?.step_index ?? 1) || 1,
        step_total: Number(question?.step_total ?? 1) || 1,
      },
    required_missing: Array.isArray(source.required_missing)
      ? source.required_missing
      : (source.summary_confirmed === true ? [] : [fieldKey]),
    next_actions: nextActions,
    actions: nextActions,
    chooser_required: source.chooser_required === true || Boolean(question || chooser || interactionNode),
    blocking: source.blocking && typeof source.blocking === 'object' && !Array.isArray(source.blocking)
      ? source.blocking
      : gate,
  } as Record<string, unknown>
}

export function useRuntimeStream(runtime: BackendRuntime, projectId: string, interactionMode: InteractionMode) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{ message: string; type: string } | null>(null)
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
        setError({ message, type: 'api' })
        handlers.onError?.({ message })
        return
      }
    }
    if (!sessionId) {
      const message = '会话未就绪，无法发送，请刷新后重试'
      setError({ message, type: 'api' })
      handlers.onError?.({ message })
      return
    }

    lastSessionIdRef.current = sessionId
    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller
    lastRequestRef.current = { content: trimmedContent, handlers, options }
    setLoading(true)
    setError(null)
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
              const bridgedPayload = toPendingPatchPayload(payload) || payload
              handlers.onNextActions?.(bridgedPayload)
              return
            }
            if (eventType === 'early_patch' || eventType === 'final_patch') {
              const bridgedPayload = toPendingPatchPayload(payload)
              if (!bridgedPayload) {
                return
              }
              handlers.onNextActions?.(bridgedPayload)
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
            if (nextCards.length > 0) {
              handlers.onUICards?.({ cards: nextCards })
            }
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
      const message = error instanceof Error ? error.message : '发送失败'
      setError({ message, type: 'api' })
      handlers.onError?.({ message })
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
      setLoading(false)
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
    setLoading(false)
  }, [])

  return { send, retry, abort, loading, error }
}
