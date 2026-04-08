type SessionRecord = {
  sessionId: string
  functionType: string
  projectId: string | null
  userId: string | null
  title: string
  status: 'active'
  preview: string
  createdAt: string
  updatedAt: string
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

export type LocalRuntime = {
  sessionAPI: {
    list: (params?: SessionListPayload) => Promise<{ sessions: SessionListItem[] }>
    get: (sessionId: string) => Promise<SessionDetail>
    create: (payload?: SessionCreatePayload) => Promise<{
      sessionId: string
      project_id: string | null
      user_id: string | null
      status: 'active'
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
  appendExchange: (sessionId: string, userMessage: string, assistantMessage: string) => void
}

type LocalRuntimeOptions = {
  defaultFunctionType?: string
  defaultSessionTitle?: string
}

function nowISO() {
  return new Date().toISOString()
}

function createId(prefix: string) {
  const randomPart = Math.random().toString(36).slice(2, 10)
  return `${prefix}_${Date.now()}_${randomPart}`
}

function toText(value: unknown) {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return ''
}

function summarizePreview(content: string, maxLength = 80) {
  const normalized = String(content || '').replace(/\s+/g, ' ').trim()
  if (!normalized) {
    return ''
  }

  if (normalized.length <= maxLength) {
    return normalized
  }

  return `${normalized.slice(0, maxLength)}...`
}

function createMessage(role: MessageRecord['role'], content: string): MessageRecord {
  return {
    message_id: createId(`msg_${role}`),
    role,
    content,
    created_at: nowISO(),
  }
}

export function createLocalRuntime({
  defaultFunctionType = 'requirement_canvas',
  defaultSessionTitle = '新会话',
}: LocalRuntimeOptions = {}): LocalRuntime {
  const sessions = new Map<string, SessionRecord>()
  const messagesBySession = new Map<string, MessageRecord[]>()

  const getMessages = (sessionId: string) => messagesBySession.get(sessionId) || []

  const getSession = (sessionId: string) => {
    const session = sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`)
    }
    return session
  }

  const touchSession = (sessionId: string) => {
    const current = getSession(sessionId)
    const messages = getMessages(sessionId)
    const latestMessage = messages.length > 0 ? messages[messages.length - 1].content : ''

    sessions.set(sessionId, {
      ...current,
      updatedAt: nowISO(),
      preview: summarizePreview(latestMessage),
    })
  }

  const sessionAPI: LocalRuntime['sessionAPI'] = {
    async list(params: SessionListPayload = {}) {
      const functionType = toText(params.function_type)
      const projectId = toText(params.project_id)
      const userId = toText(params.user_id)

      const list: SessionListItem[] = Array.from(sessions.values())
        .filter((item) => !functionType || item.functionType === functionType)
        .filter((item) => !projectId || item.projectId === projectId)
        .filter((item) => !userId || item.userId === userId)
        .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
        .map((item) => ({
          sessionId: item.sessionId,
          project_id: item.projectId,
          user_id: item.userId,
          title: item.title,
          status: item.status,
          updatedAt: item.updatedAt,
          preview: item.preview,
        }))

      return { sessions: list }
    },

    async get(sessionId: string): Promise<SessionDetail> {
      const session = getSession(sessionId)
      return {
        sessionId: session.sessionId,
        project_id: session.projectId,
        user_id: session.userId,
        function_type: session.functionType,
        title: session.title,
        status: session.status,
      }
    },

    async create(payload: SessionCreatePayload = {}) {
      const nextSessionId = createId('sess')
      const now = nowISO()

      const record: SessionRecord = {
        sessionId: nextSessionId,
        functionType: toText(payload.function_type) || defaultFunctionType,
        projectId: toText(payload.project_id) || null,
        userId: toText(payload.user_id) || null,
        title: toText(payload.title) || defaultSessionTitle,
        status: 'active',
        preview: '',
        createdAt: now,
        updatedAt: now,
      }

      sessions.set(nextSessionId, record)
      messagesBySession.set(nextSessionId, [])

      return {
        sessionId: nextSessionId,
        project_id: record.projectId,
        user_id: record.userId,
        status: record.status,
      }
    },

    async update(sessionId: string, payload: SessionUpdatePayload = {}) {
      const session = getSession(sessionId)
      const nextTitle = toText(payload.title) || session.title

      sessions.set(sessionId, {
        ...session,
        title: nextTitle,
        updatedAt: nowISO(),
      })

      return {
        sessionId,
        title: nextTitle,
      }
    },
  }

  const messageAPI: LocalRuntime['messageAPI'] = {
    async list(sessionId: string) {
      return {
        messages: getMessages(sessionId).map((message) => ({ ...message })),
      }
    },
  }

  const appendExchange = (sessionId: string, userMessage: string, assistantMessage: string) => {
    const nextMessages = [...getMessages(sessionId)]
    nextMessages.push(createMessage('user', userMessage))
    nextMessages.push(createMessage('assistant', assistantMessage))
    messagesBySession.set(sessionId, nextMessages)
    touchSession(sessionId)
  }

  return {
    sessionAPI,
    messageAPI,
    appendExchange,
  }
}
