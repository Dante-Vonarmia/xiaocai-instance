/**
 * Chat Hook
 *
 * 职责:
 * 1. 管理对话状态（消息列表、会话 ID）
 * 2. 提供发送消息接口
 * 3. 处理流式响应
 *
 * 业务流程:
 * 1. 用户发送消息
 * 2. 调用 /chat/run 或 /chat/stream
 * 3. 更新消息列表
 * 4. 渲染 UI cards（由 FLARE chat-ui 处理）
 *
 * 参考:
 * - docs/discussions/phase-1-procurement-product-logic.md
 *   需求梳理、智能寻源等业务流程
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  chatApi,
  type ChatCard,
  type ChatRequestPayload,
} from '@/services/api'

/**
 * 消息类型
 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  cards?: ChatCard[]
  timestamp: number
}

type MessageRole = ChatMessage['role']
type ChatContext = Record<string, unknown>

let messageSeed = 0

function createMessageId(prefix: string) {
  messageSeed += 1
  return `${prefix}-${Date.now()}-${messageSeed}`
}

function createMessage(role: MessageRole, content: string, cards?: ChatCard[]): ChatMessage {
  return {
    id: createMessageId(role),
    role,
    content,
    cards,
    timestamp: Date.now(),
  }
}

function patchMessage(
  messages: ChatMessage[],
  messageId: string,
  patch: Partial<Pick<ChatMessage, 'content' | 'cards'>>,
) {
  return messages.map((message) => (
    message.id === messageId
      ? {
          ...message,
          ...patch,
        }
      : message
  ))
}

function formatChatError(error: unknown) {
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  if (typeof error === 'string' && error.trim()) {
    return error.trim()
  }

  return '发送消息失败'
}

function isAbortError(error: unknown) {
  return error instanceof Error && error.name === 'AbortError'
}

/**
 * useChat Hook
 */
export function useChat(sessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string>(
    sessionId || `session-${Date.now()}`
  )
  const requestIdRef = useRef(0)
  const abortControllerRef = useRef<AbortController | null>(null)

  const beginRequest = useCallback(() => {
    requestIdRef.current += 1
    setIsLoading(true)
    setError(null)
    return requestIdRef.current
  }, [])

  const endRequest = useCallback((requestId: number) => {
    if (requestIdRef.current === requestId) {
      setIsLoading(false)
    }
  }, [])

  /**
   * 发送消息 - 同步模式
   */
  const sendMessage = useCallback(async (content: string, context?: ChatContext) => {
    const trimmedContent = content.trim()
    if (!trimmedContent) {
      return null
    }

    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    const requestId = beginRequest()
    const userMessage = createMessage('user', trimmedContent)
    const assistantMessage = createMessage('assistant', '')

    setMessages((prev) => [...prev, userMessage])

    try {
      const response = await chatApi.run({
        message: trimmedContent,
        session_id: currentSessionId,
        context,
      }, {
        signal: controller.signal,
      })

      setMessages((prev) => [
        ...prev,
        {
          ...assistantMessage,
          content: response.message,
          cards: response.cards,
        },
      ])

      return response
    } catch (error) {
      const message = formatChatError(error)
      if (!isAbortError(error)) {
        setError(message)
      }

      return Promise.reject(error)
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
      endRequest(requestId)
    }
  }, [beginRequest, currentSessionId, endRequest])

  /**
   * 发送消息 - 流式模式
   */
  const sendMessageStream = useCallback(async (content: string, context?: ChatContext) => {
    const trimmedContent = content.trim()
    if (!trimmedContent) {
      return null
    }

    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    const requestId = beginRequest()
    const userMessage = createMessage('user', trimmedContent)
    const assistantMessageId = createMessageId('assistant')
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant' as const,
      content: '',
      cards: [] as ChatCard[],
      timestamp: Date.now(),
    }

    let streamedContent = ''
    let streamedCards: ChatCard[] = []

    setMessages((prev) => [...prev, userMessage, assistantMessage])

    try {
      const response = await chatApi.stream(
        {
          message: trimmedContent,
          session_id: currentSessionId,
          context,
        } satisfies ChatRequestPayload,
        {
          signal: controller.signal,
          onChunk: (chunk) => {
            streamedContent += chunk
            setMessages((prev) => patchMessage(prev, assistantMessageId, { content: streamedContent }))
          },
          onCard: (card) => {
            streamedCards = [...streamedCards, card]
            setMessages((prev) => patchMessage(prev, assistantMessageId, { cards: streamedCards }))
          },
        },
      )

      const finalContent = response.message || streamedContent
      const finalCards = response.cards.length > 0 ? response.cards : streamedCards

      setMessages((prev) => patchMessage(prev, assistantMessageId, {
        content: finalContent,
        cards: finalCards,
      }))

      return response
    } catch (error) {
      if (!isAbortError(error)) {
        const message = formatChatError(error)
        setError(message)
        setMessages((prev) => patchMessage(prev, assistantMessageId, {
          content: `发送失败：${message}`,
          cards: [],
        }))
      }

      return Promise.reject(error)
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
      endRequest(requestId)
    }
  }, [beginRequest, currentSessionId, endRequest])

  /**
   * 清空消息
   */
  const clearMessages = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    setMessages([])
    setError(null)
    setIsLoading(false)
  }, [])

  /**
   * 重新开始会话
   */
  const resetSession = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    setCurrentSessionId(`session-${Date.now()}`)
    setMessages([])
    setError(null)
    setIsLoading(false)
  }, [])

  useEffect(() => () => {
    abortControllerRef.current?.abort()
  }, [])

  return {
    messages,
    isLoading,
    error,
    sessionId: currentSessionId,
    sendMessage,
    sendMessageStream,
    clearMessages,
    resetSession,
  }
}
