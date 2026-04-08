import { messageApi, sessionApi, type MessageRecord, type SessionCreatePayload, type SessionDetail, type SessionListItem, type SessionListPayload, type SessionUpdatePayload } from '@/services/api'

export type BackendRuntime = {
  sessionAPI: {
    list: (params?: SessionListPayload) => Promise<{ sessions: SessionListItem[] }>
    get: (sessionId: string) => Promise<SessionDetail>
    create: (payload?: SessionCreatePayload) => Promise<{
      sessionId: string
      project_id: string | null
      user_id: string | null
      status: 'active'
    }>
    delete: (sessionId: string) => Promise<{
      deleted: boolean
    }>
    update: (
      sessionId: string,
      payload?: SessionUpdatePayload,
    ) => Promise<{
      sessionId: string
      title: string
    }>
  }
  messageAPI: {
    list: (sessionId: string) => Promise<{ messages: MessageRecord[] }>
  }
  appendExchange: (sessionId: string, userMessage: string, assistantMessage: string) => Promise<void>
}

export function createBackendRuntime(): BackendRuntime {
  return {
    sessionAPI: {
      async list(params = {}) {
        return sessionApi.list(params)
      },
      async get(sessionId: string) {
        return sessionApi.get(sessionId)
      },
      async create(payload = {}) {
        return sessionApi.create(payload)
      },
      async delete(sessionId: string) {
        return sessionApi.delete(sessionId)
      },
      async update(sessionId: string, payload = {}) {
        return sessionApi.update(sessionId, payload)
      },
    },
    messageAPI: {
      async list(sessionId: string) {
        return messageApi.list(sessionId)
      },
    },
    async appendExchange(sessionId: string, userMessage: string, assistantMessage: string) {
      await messageApi.appendExchange(sessionId, userMessage, assistantMessage)
    },
  }
}
