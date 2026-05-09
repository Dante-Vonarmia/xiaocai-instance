import { apiClient, messageApi, sessionApi, type MessageRecord, type SessionCreatePayload, type SessionDetail, type SessionListItem, type SessionListPayload, type SessionUpdatePayload } from '@/services/api'

type ProjectRecord = {
  project_id: string
  project_name: string
  status: string
  session_count?: number
  latest_updated_at?: string
}

type AppendExchangePayload = {
  user_message?: unknown
  assistant_message?: unknown
}

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
      status: 'active' | 'archived'
    }>
  }
  messageAPI: {
    list: (sessionId: string) => Promise<{ messages: MessageRecord[] }>
    appendExchange: (sessionId: string, payload?: AppendExchangePayload) => Promise<{ success: boolean }>
  }
  projectAPI: {
    listProjects: () => Promise<{ projects: ProjectRecord[] }>
    upsertProject: (
      projectId: string,
      payload?: { project_name?: string | null; status?: string },
    ) => Promise<ProjectRecord>
  }
  appendExchange: (sessionId: string, userMessage: string, assistantMessage: string) => Promise<void>
}

function toText(value: unknown) {
  return typeof value === 'string' ? value.trim() : ''
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
      async appendExchange(sessionId: string, payload = {}) {
        await messageApi.appendExchange(
          sessionId,
          toText(payload.user_message),
          toText(payload.assistant_message),
        )
        return { success: true }
      },
    },
    projectAPI: {
      async listProjects() {
        const response = await apiClient.get('/projects')
        const payload = response.data as { projects?: ProjectRecord[] }
        return { projects: Array.isArray(payload.projects) ? payload.projects : [] }
      },
      async upsertProject(projectId: string, payload = {}) {
        const response = await apiClient.put(`/projects/${encodeURIComponent(projectId)}`, {
          project_name: payload.project_name ?? null,
          status: payload.status ?? 'active',
        })
        return response.data as ProjectRecord
      },
    },
    async appendExchange(sessionId: string, userMessage: string, assistantMessage: string) {
      await messageApi.appendExchange(sessionId, userMessage, assistantMessage)
    },
  }
}
