import { apiClient } from '@/services/api'

export type DomainInjectionMode = 'off' | 'assist' | 'enforce'
export type ConnectorState = 'connected' | 'disconnected' | 'error'

export type ConnectorStatus = {
  key: string
  name: string
  enabled: boolean
  status: ConnectorState
  health: string
  latency_ms: number | null
  last_success_at: string | null
  last_error: string
  scope: string
  updated_at: string
  updated_by: string
}

export type SettingsIntegrationsResponse = {
  domain_injection_mode: DomainInjectionMode
  connectors: ConnectorStatus[]
}

export const settingsApi = {
  getIntegrations: async () => {
    const response = await apiClient.get('/settings/integrations')
    return response.data as SettingsIntegrationsResponse
  },

  setDomainInjectionMode: async (domainInjectionMode: DomainInjectionMode) => {
    const response = await apiClient.patch('/settings/domain-injection-mode', {
      domain_injection_mode: domainInjectionMode,
    })
    return response.data as SettingsIntegrationsResponse
  },

  setConnectorEnabled: async (key: string, enabled: boolean) => {
    const response = await apiClient.patch(`/settings/connectors/${key}`, { enabled })
    return response.data as ConnectorStatus
  },

  testConnector: async (key: string) => {
    const response = await apiClient.post(`/settings/connectors/${key}/test`)
    return response.data as ConnectorStatus
  },
}
