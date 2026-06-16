import apiClient from '@/services/api'

type JsonRecord = Record<string, unknown>

export async function exchangeCaigouChinaCredential(credential: string) {
  const response = await apiClient.post('/auth/exchange', {
    mock: false,
    credential,
  })
  return response.data as JsonRecord
}
