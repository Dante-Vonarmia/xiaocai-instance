/**
 * API 客户端
 *
 * 职责:
 * 1. 封装所有 HTTP 请求
 * 2. 管理认证 token
 * 3. 处理错误
 */

import axios, { AxiosHeaders, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

type JsonRecord = Record<string, unknown>
export type ChatCard = JsonRecord

export interface ChatRequestPayload {
  message: string
  session_id: string
  context?: JsonRecord
}

export interface ChatRunResponse {
  message: string
  session_id: string
  cards: ChatCard[]
  metadata: JsonRecord
}

export interface ChatStreamEvent {
  type: string
  data: unknown
  raw: string
}

export interface ChatStreamCallbacks {
  signal?: AbortSignal
  onChunk?: (chunk: string, event: ChatStreamEvent) => void
  onCard?: (card: JsonRecord, event: ChatStreamEvent) => void
  onEvent?: (event: ChatStreamEvent) => void
  onComplete?: (result: ChatRunResponse) => void
  onError?: (error: ApiError) => void
}

export type SessionCreatePayload = {
  function_type?: string
  title?: string
  project_id?: string
  user_id?: string
}

export type SessionListPayload = {
  function_type?: string
  project_id?: string
  user_id?: string
}

export type SessionUpdatePayload = {
  title?: string
}

export type SessionListItem = {
  sessionId: string
  project_id: string | null
  user_id: string | null
  title: string
  status: 'active'
  updatedAt: string
  preview: string
}

export type SessionDetail = {
  sessionId: string
  project_id: string | null
  user_id: string | null
  function_type: string
  title: string
  status: 'active'
}

export type MessageRecord = {
  message_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

const ACCESS_TOKEN_KEY = 'access_token'
const CURRENT_USER_ID_KEY = 'current_user_id'
const AUTH_CHANGED_EVENT = 'xiaocai-auth-change'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function canUseBrowserStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function getAccessToken() {
  if (!canUseBrowserStorage()) {
    return ''
  }

  try {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setAccessToken(token: string) {
  if (!canUseBrowserStorage()) {
    return
  }

  window.localStorage.setItem(ACCESS_TOKEN_KEY, token.trim())
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
}

export function getCurrentUserId() {
  if (!canUseBrowserStorage()) {
    return ''
  }

  try {
    return window.localStorage.getItem(CURRENT_USER_ID_KEY) || ''
  } catch {
    return ''
  }
}

export function setCurrentUserId(userId: string) {
  if (!canUseBrowserStorage()) {
    return
  }

  window.localStorage.setItem(CURRENT_USER_ID_KEY, userId.trim())
}

export function clearCurrentUserId() {
  if (!canUseBrowserStorage()) {
    return
  }

  window.localStorage.removeItem(CURRENT_USER_ID_KEY)
}

export function clearAccessToken() {
  if (!canUseBrowserStorage()) {
    return
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
}

export class ApiError extends Error {
  status?: number
  details?: unknown
  code?: string

  constructor(message: string, options: { status?: number; details?: unknown; code?: string } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.details = options.details
    this.code = options.code
  }
}

function isPlainObject(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function getMessageFromUnknown(value: unknown, fallback: string) {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }

  if (isPlainObject(value)) {
    const candidates = [value.message, value.detail, value.error, value.msg]
    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return candidate.trim()
      }
    }
  }

  return fallback
}

function buildUrl(pathname: string) {
  if (!API_BASE_URL) {
    return pathname
  }

  return `${API_BASE_URL.replace(/\/+$/, '')}/${pathname.replace(/^\/+/, '')}`
}

function buildAuthHeaders(init?: HeadersInit) {
  const headers = new Headers(init)
  const token = getAccessToken()

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return headers
}

function normalizeAxiosError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const payload = error.response?.data

    if (status === 401) {
      clearAccessToken()
    }

    return new ApiError(
      getMessageFromUnknown(
        payload,
        error.message || (status ? `HTTP ${status}` : '请求失败'),
      ),
      {
        status,
        details: payload,
        code: error.code,
      },
    )
  }

  if (error instanceof ApiError) {
    return error
  }

  if (error instanceof Error) {
    return new ApiError(error.message)
  }

  return new ApiError('请求失败')
}

async function parseJsonResponse(response: Response) {
  const text = await response.text()
  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

async function createApiErrorFromResponse(response: Response) {
  const payload = await parseJsonResponse(response)

  if (response.status === 401) {
    clearAccessToken()
  }

  if (isPlainObject(payload)) {
    return new ApiError(
      getMessageFromUnknown(payload, `HTTP ${response.status}: ${response.statusText}`),
      {
        status: response.status,
        details: payload,
      },
    )
  }

  return new ApiError(
    getMessageFromUnknown(payload, `HTTP ${response.status}: ${response.statusText}`),
    {
      status: response.status,
      details: payload,
    },
  )
}

function parseSsePayload(rawData: string) {
  const trimmed = rawData.trim()
  if (!trimmed) {
    return ''
  }

  try {
    return JSON.parse(trimmed) as unknown
  } catch {
    return trimmed
  }
}

function extractTextField(payload: unknown, keys: string[]) {
  if (!isPlainObject(payload)) {
    return ''
  }

  for (const key of keys) {
    const candidate = payload[key]
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim()
    }
  }

  return ''
}

function extractRecordField(payload: unknown, keys: string[]) {
  if (!isPlainObject(payload)) {
    return null
  }

  for (const key of keys) {
    const candidate = payload[key]
    if (isPlainObject(candidate)) {
      return candidate
    }
  }

  return null
}

function extractCardList(payload: unknown) {
  if (!isPlainObject(payload)) {
    return []
  }

  const candidate = payload.cards
  if (!Array.isArray(candidate)) {
    return []
  }

  return candidate.filter(isPlainObject)
}

function toUiCardsPayload(cards: JsonRecord[]) {
  return {
    type: 'ui_cards',
    cards,
  }
}

function resolveStreamEventType(payload: unknown, fallbackType: string) {
  if (isPlainObject(payload) && typeof payload.type === 'string' && payload.type.trim()) {
    return payload.type.trim()
  }

  return fallbackType || 'message'
}

function normalizeStreamEvent(
  payload: unknown,
  fallbackType: string,
  state: {
    message: string
    cards: JsonRecord[]
    metadata: JsonRecord
    sessionId: string
  },
) {
  const eventType = resolveStreamEventType(payload, fallbackType)
  const normalizedType = eventType.toLowerCase()

  if (normalizedType === 'chunk' || normalizedType === 'token' || normalizedType === 'content') {
    const chunk = extractTextField(payload, ['delta', 'chunk', 'content', 'text'])
    if (chunk) {
      state.message += chunk
      return { kind: 'chunk' as const, chunk }
    }
  }

  if (normalizedType === 'card') {
    const card = extractRecordField(payload, ['card_data', 'card', 'data'])
    if (card) {
      state.cards.push(card)
      return { kind: 'card' as const, card }
    }
  }

  if (normalizedType === 'ui_cards' || normalizedType === 'cards') {
    const cards = extractCardList(payload)
    if (cards.length > 0) {
      state.cards = cards
      return { kind: 'cards' as const, cards }
    }
  }

  if (normalizedType === 'recovery_plan' || normalizedType === 'capability_suggestion') {
    if (isPlainObject(payload)) {
      const card = {
        type: normalizedType,
        payload,
      }
      state.cards.push(card)
      return { kind: 'card' as const, card }
    }
  }

  if (normalizedType === 'done' || normalizedType === 'complete') {
    const finalMessage = extractTextField(payload, ['final_message', 'message'])
    const sessionId = extractTextField(payload, ['session_id'])
    const metadata = extractRecordField(payload, ['metadata'])

    if (finalMessage) {
      state.message = finalMessage
    }

    if (sessionId) {
      state.sessionId = sessionId
    }

    if (metadata) {
      state.metadata = metadata
    }

    return { kind: 'done' as const }
  }

  if (normalizedType === 'error') {
    throw new ApiError(
      getMessageFromUnknown(payload, '流式请求失败'),
      {
        details: payload,
      },
    )
  }

  if (isPlainObject(payload)) {
    const chunk = extractTextField(payload, ['delta', 'chunk', 'content', 'text', 'message'])
    if (chunk) {
      state.message += chunk
      return { kind: 'chunk' as const, chunk }
    }

    const card = extractRecordField(payload, ['card_data', 'card', 'data'])
    if (card) {
      state.cards.push(card)
      return { kind: 'card' as const, card }
    }

    const cards = extractCardList(payload)
    if (cards.length > 0) {
      state.cards = cards
      return { kind: 'cards' as const, cards }
    }
  }

  if (typeof payload === 'string' && payload.trim()) {
    state.message += payload
    return { kind: 'chunk' as const, chunk: payload }
  }

  return null
}

async function consumeSseBody(
  response: Response,
  callbacks: ChatStreamCallbacks,
  requestSessionId: string,
) {
  if (!response.body) {
    throw new ApiError('当前环境不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  const state = {
    message: '',
    cards: [] as JsonRecord[],
    metadata: {} as JsonRecord,
    sessionId: requestSessionId,
  }

  let currentEventType = ''
  let currentDataLines: string[] = []
  let textBuffer = ''

  const emitCurrentEvent = () => {
    if (!currentEventType && currentDataLines.length === 0) {
      return null
    }

    const fallbackType = currentEventType || 'message'
    const rawData = currentDataLines.join('\n')
    currentEventType = ''
    currentDataLines = []

    const data = parseSsePayload(rawData)
    const event: ChatStreamEvent = {
      type: resolveStreamEventType(data, fallbackType),
      data,
      raw: rawData,
    }

    callbacks.onEvent?.(event)

    const result = normalizeStreamEvent(data, event.type, state)
    if (!result) {
      return null
    }

    if (result.kind === 'chunk') {
      callbacks.onChunk?.(result.chunk, event)
    } else if (result.kind === 'card') {
      callbacks.onCard?.(toUiCardsPayload([result.card]), event)
    } else if (result.kind === 'cards') {
      callbacks.onCard?.(toUiCardsPayload(result.cards), event)
    }

    return result
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      textBuffer += decoder.decode(value || new Uint8Array(), { stream: !done })

      if (done) {
        const remainingLines = textBuffer.split(/\r?\n/)
        textBuffer = ''
        for (const line of remainingLines) {
          if (!line) {
            emitCurrentEvent()
            continue
          }

          if (line.startsWith('event:')) {
            currentEventType = line.slice(6).trim()
            continue
          }

          if (line.startsWith('data:')) {
            currentDataLines.push(line.slice(5).replace(/^\s/, ''))
          }
        }

        emitCurrentEvent()
        break
      }

      const lines = textBuffer.split(/\r?\n/)
      textBuffer = lines.pop() || ''
      if (lines.length === 0) {
        continue
      }

      for (const line of lines) {
        if (!line) {
          emitCurrentEvent()
          continue
        }

        if (line.startsWith('event:')) {
          currentEventType = line.slice(6).trim()
          continue
        }

        if (line.startsWith('data:')) {
          currentDataLines.push(line.slice(5).replace(/^\s/, ''))
        }
      }
    }
  } catch (error) {
    if ((error as Error)?.name === 'AbortError') {
      throw error
    }

    throw normalizeAxiosError(error)
  }

  const result: ChatRunResponse = {
    message: state.message,
    session_id: state.sessionId,
    cards: state.cards,
    metadata: state.metadata,
  }

  callbacks.onComplete?.(result)
  return result
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const headers = AxiosHeaders.from(config.headers)
    const token = getAccessToken()

    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    config.headers = headers
    return config
  },
  (error) => Promise.reject(normalizeAxiosError(error)),
)

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeAxiosError(error)),
)

export const authApi = {
  exchangeTokenMock: async (mockUserId: string) => {
    const response = await apiClient.post('/auth/exchange', {
      mock: true,
      mock_user_id: mockUserId,
    })
    return response.data as JsonRecord
  },

  exchangeTokenHost: async (hostToken: string) => {
    const response = await apiClient.post('/auth/exchange', {
      mock: false,
      host_token: hostToken,
    })
    return response.data as JsonRecord
  },

  exchangeTokenWechat: async (wechatCode: string) => {
    const response = await apiClient.post('/auth/exchange', {
      mock: false,
      wechat_code: wechatCode,
    })
    return response.data as JsonRecord
  },
}

export const chatApi = {
  run: async (params: ChatRequestPayload, options: { signal?: AbortSignal } = {}) => {
    const response = await apiClient.post('/chat/run', params, {
      signal: options.signal,
    })
    return response.data as ChatRunResponse
  },

  stream: async (params: ChatRequestPayload, callbacks: ChatStreamCallbacks = {}) => {
    const response = await fetch(buildUrl('/chat/stream'), {
      method: 'POST',
      headers: buildAuthHeaders({
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      }),
      body: JSON.stringify(params),
      signal: callbacks.signal,
    })

    if (!response.ok) {
      const apiError = await createApiErrorFromResponse(response)
      callbacks.onError?.(apiError)
      throw apiError
    }

    try {
      return await consumeSseBody(response, callbacks, params.session_id)
    } catch (error) {
      if (error instanceof ApiError) {
        callbacks.onError?.(error)
        throw error
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw error
      }

      const apiError = normalizeAxiosError(error)
      callbacks.onError?.(apiError)
      throw apiError
    }
  },
}

export const sessionApi = {
  list: async (params: SessionListPayload = {}) => {
    const response = await apiClient.get('/sessions', { params })
    return response.data as {
      sessions: SessionListItem[]
      pagination?: {
        page: number
        page_size: number
        total: number
        total_pages: number
      }
      grouped?: {
        today: SessionListItem[]
        last_7_days: SessionListItem[]
        earlier: SessionListItem[]
      }
    }
  },
  get: async (sessionId: string) => {
    const response = await apiClient.get(`/sessions/${sessionId}`)
    return response.data as SessionDetail
  },
  create: async (payload: SessionCreatePayload = {}) => {
    const response = await apiClient.post('/sessions', payload)
    return response.data as {
      sessionId: string
      project_id: string | null
      user_id: string | null
      status: 'active'
    }
  },
  update: async (sessionId: string, payload: SessionUpdatePayload = {}) => {
    const response = await apiClient.patch(`/sessions/${sessionId}`, payload)
    return response.data as { sessionId: string; title: string }
  },
  delete: async (sessionId: string) => {
    const response = await apiClient.delete(`/sessions/${sessionId}`)
    return response.data as { deleted: boolean }
  },
}

export const messageApi = {
  list: async (sessionId: string) => {
    const response = await apiClient.get(`/sessions/${sessionId}/messages`)
    const payload = response.data as { messages: MessageRecord[] }
    const messages = Array.isArray(payload.messages) ? payload.messages : []
    const hasUserMessage = messages.some((item) => item?.role === 'user')

    if (!hasUserMessage) {
      return { messages: [] }
    }

    return { messages }
  },
  appendExchange: async (sessionId: string, userMessage: string, assistantMessage: string) => {
    const response = await apiClient.post(`/sessions/${sessionId}/messages/append`, {
      user_message: userMessage,
      assistant_message: assistantMessage,
    })
    return response.data as { success: boolean }
  },
}

export const sourceApi = {
  uploadSourceFile: async (payload: { file: File; project_id: string; session_id?: string; folder_name?: string }) => {
    const form = new FormData()
    form.append('file', payload.file)
    form.append('project_id', payload.project_id)
    if (payload.session_id) {
      form.append('session_id', payload.session_id)
    }
    if (payload.folder_name && payload.folder_name.trim()) {
      form.append('folder_name', payload.folder_name.trim())
    }
    const response = await apiClient.post('/sources/upload', form, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data as Record<string, unknown>
  },
  listProjectSources: async (projectId: string, options: { q?: string; folder_name?: string } = {}) => {
    const response = await apiClient.get('/sources', {
      params: {
        project_id: projectId,
        q: options.q || undefined,
        folder_name: options.folder_name || undefined,
      },
    })
    return response.data as {
      project_id: string
      query?: string
      folder_name?: string
      sources: Record<string, unknown>[]
    }
  },
  listProjectSourceFolders: async (projectId: string) => {
    const response = await apiClient.get('/sources/folders', {
      params: { project_id: projectId },
    })
    return response.data as {
      project_id: string
      folders: Array<{
        folder_name: string
        file_count: number
        referenced_count: number
      }>
    }
  },
  markSourceReferenced: async (projectId: string, sourceId: string) => {
    const response = await apiClient.post(`/sources/${sourceId}/mark-referenced`, null, {
      params: { project_id: projectId },
    })
    return response.data as {
      marked: boolean
      source_id: string
      status: string
    }
  },
  deleteProjectSource: async (projectId: string, sourceId: string) => {
    const response = await apiClient.delete(`/sources/${sourceId}`, {
      params: { project_id: projectId },
    })
    return response.data as { deleted: boolean }
  },
}

export const projectApi = {
  bindProject: async (projectId: string) => {
    const response = await apiClient.post('/projects/bind', {
      project_id: projectId,
    })
    return response.data as {
      success: boolean
      user_id: string
      project_id: string
    }
  },
  listMine: async () => {
    const response = await apiClient.get('/projects/mine')
    return response.data as {
      project_ids: string[]
    }
  },
  usage: async (projectId?: string) => {
    const response = await apiClient.get('/projects/usage', {
      params: {
        project_id: projectId || undefined,
      },
    })
    return response.data as {
      user_id: string
      project_id: string | null
      day_start_utc: string
      daily_message_limit: number
      daily_message_used: number
      daily_message_remaining: number | null
      daily_project_message_limit: number
      daily_project_message_used: number | null
      daily_project_message_remaining: number | null
    }
  },
}

export { apiClient }

export default apiClient
