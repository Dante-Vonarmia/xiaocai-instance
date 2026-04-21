import { apiClient, authApi, sourceApi } from '@/services/api'

type DomainFieldsResponse = Record<string, unknown>

type AuthExchangeMode = 'mock' | 'host_token' | 'wechat_code'

type UploadSourcePayload = {
  file: File
  project_id: string
  session_id?: string
  folder_name?: string
}

async function getDomainFields(domain: string): Promise<DomainFieldsResponse> {
  const normalized = String(domain || '').trim()
  if (!normalized) {
    return {
      domain: '',
      fields: [],
    }
  }

  try {
    const response = await apiClient.get(`/v1/domains/${encodeURIComponent(normalized)}/fields`)
    return response.data as DomainFieldsResponse
  } catch {
    const fallbackResponse = await apiClient.get(`/domains/${encodeURIComponent(normalized)}/fields`)
    return fallbackResponse.data as DomainFieldsResponse
  }
}

async function authExchange(
  mode: AuthExchangeMode,
  value: string,
): Promise<Record<string, unknown>> {
  if (mode === 'host_token') {
    return authApi.exchangeTokenHost(value)
  }
  if (mode === 'wechat_code') {
    return authApi.exchangeTokenWechat(value)
  }
  return authApi.exchangeTokenMock(value)
}

async function uploadFile(payload: UploadSourcePayload): Promise<Record<string, unknown>> {
  return sourceApi.uploadSourceFile(payload)
}

export const instanceApi = {
  getDomainFields,
  authExchange,
  uploadFile,
}

export const instanceSourceApi = {
  ...sourceApi,
  getDomainFields,
}

