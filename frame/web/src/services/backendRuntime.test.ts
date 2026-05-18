import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createBackendRuntime } from '@/services/backendRuntime'
import { messageApi } from '@/services/api'

const apiMocks = vi.hoisted(() => ({
  get: vi.fn(),
  put: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  apiClient: {
    get: apiMocks.get,
    put: apiMocks.put,
  },
  messageApi: {
    appendExchange: vi.fn(),
    list: vi.fn(),
  },
  sessionApi: {
    create: vi.fn(),
    delete: vi.fn(),
    get: vi.fn(),
    list: vi.fn(),
    update: vi.fn(),
  },
}))

describe('createBackendRuntime projectAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('normalizes project list records for FLARE core editing', async () => {
    apiMocks.get.mockResolvedValue({
      data: {
        projects: [
          {
            project_id: 'project-1',
            project_name: '采购项目 A',
            status: 'active',
            session_count: 2,
            created_at: '2026-05-09T00:00:00Z',
            latest_updated_at: '2026-05-09T01:00:00Z',
          },
        ],
      },
    })

    const runtime = createBackendRuntime()
    const result = await runtime.projectAPI.listProjects()

    expect(result.projects[0]).toMatchObject({
      key: 'project-1',
      id: 'project-1',
      project_id: 'project-1',
      project_name: '采购项目 A',
      name: '采购项目 A',
      status: 'active',
      createdAt: '2026-05-09T00:00:00Z',
      updatedAt: '2026-05-09T01:00:00Z',
    })
  })

  it('normalizes renamed project response for FLARE core projection', async () => {
    apiMocks.put.mockResolvedValue({
      data: {
        project_id: 'project-1',
        project_name: '采购项目 B',
        status: 'active',
      },
    })

    const runtime = createBackendRuntime()
    const result = await runtime.projectAPI.upsertProject('project-1', {
      project_name: '采购项目 B',
    })

    expect(apiMocks.put).toHaveBeenCalledWith('/projects/project-1', {
      project_name: '采购项目 B',
      status: 'active',
    })
    expect(result).toMatchObject({
      key: 'project-1',
      project_id: 'project-1',
      name: '采购项目 B',
    })
  })

  it('preserves FLARE appendExchange artifacts for history reload', async () => {
    const payload = {
      user_message: '我要采购测试服务器',
      assistant_message: '# 需求梳理草稿',
      canvas_state: {
        progress: 0.25,
      },
    }

    const runtime = createBackendRuntime()
    await runtime.messageAPI.appendExchange('session-1', payload)

    expect(messageApi.appendExchange).toHaveBeenCalledWith('session-1', payload)
  })
})
