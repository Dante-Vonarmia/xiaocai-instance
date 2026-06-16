import apiClient from '@/services/api'

type JsonRecord = Record<string, unknown>

export async function exchangeCaigouChinaTicket(loginTicket: string) {
  const response = await apiClient.post('/auth/exchange', {
    mock: false,
    login_ticket: loginTicket,
  })
  return response.data as JsonRecord
}
