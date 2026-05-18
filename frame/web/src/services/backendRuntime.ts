import {
  apiClient,
  type AppendExchangePayload,
  messageApi,
  sessionApi,
  type MessageRecord,
  type SessionCreatePayload,
  type SessionDetail,
  type SessionListItem,
  type SessionListPayload,
  type SessionUpdatePayload,
} from '@/services/api'

type ProjectRecord = {
  key: string
  id: string
  project_id: string
  project_name: string
  name: string
  status: string
  session_count: number
  created_at: string
  latest_updated_at: string
  createdAt: string
  updatedAt: string
}

type ProjectApiRecord = {
  key?: unknown
  id?: unknown
  project_id?: unknown
  projectId?: unknown
  project_name?: unknown
  projectName?: unknown
  name?: unknown
  status?: unknown
  session_count?: unknown
  created_at?: unknown
  createdAt?: unknown
  updated_at?: unknown
  updatedAt?: unknown
  latest_updated_at?: unknown
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

function toCount(value: unknown) {
  const count = Number(value)
  return Number.isFinite(count) ? count : 0
}

/**
 * Adapter boundary: FLARE core project UI requires `key/name` while xiaocai
 * API owns `project_id/project_name`. Keep that projection here, not in UI.
 */
function normalizeProjectRecord(record: ProjectApiRecord): ProjectRecord {
  const projectId = toText(record.project_id)
    || toText(record.projectId)
    || toText(record.id)
    || toText(record.key)
  const projectName = toText(record.project_name)
    || toText(record.projectName)
    || toText(record.name)
    || projectId
  const createdAt = toText(record.created_at) || toText(record.createdAt)
  const updatedAt = toText(record.latest_updated_at)
    || toText(record.updated_at)
    || toText(record.updatedAt)
    || createdAt

  return {
    key: projectId,
    id: projectId,
    project_id: projectId,
    project_name: projectName,
    name: projectName,
    status: toText(record.status) || 'active',
    session_count: toCount(record.session_count),
    created_at: createdAt,
    latest_updated_at: updatedAt,
    createdAt,
    updatedAt,
  }
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
        await messageApi.appendExchange(sessionId, payload)
        return { success: true }
      },
    },
    projectAPI: {
      async listProjects() {
        const response = await apiClient.get('/projects')
        const payload = response.data as { projects?: ProjectApiRecord[] }
        const projects = Array.isArray(payload.projects) ? payload.projects : []
        return {
          projects: projects
            .map(normalizeProjectRecord)
            .filter((project) => Boolean(project.project_id)),
        }
      },
      async upsertProject(projectId: string, payload = {}) {
        const response = await apiClient.put(`/projects/${encodeURIComponent(projectId)}`, {
          project_name: payload.project_name ?? null,
          status: payload.status ?? 'active',
        })
        return normalizeProjectRecord(response.data as ProjectApiRecord)
      },
    },
    async appendExchange(sessionId: string, userMessage: string, assistantMessage: string) {
      await messageApi.appendExchange(sessionId, userMessage, assistantMessage)
    },
  }
}
