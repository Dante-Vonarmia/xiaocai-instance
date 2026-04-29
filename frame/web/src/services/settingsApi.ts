import { apiClient } from '@/services/api'

export type DomainInjectionMode = 'off' | 'assist' | 'enforce'
export type ConnectorState = 'connected' | 'disconnected' | 'error'
export type ConnectorType = 'database' | 'knowledge' | 'search' | 'mcp'

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

export type ConnectorRegistryItem = ConnectorStatus & {
  connector_id: string
  connector_type: ConnectorType
  driver: string
  priority: number
  config_json: Record<string, unknown>
  tags_json: string[]
}

export type ConnectorRegistryListResponse = {
  connectors: ConnectorRegistryItem[]
}

export type ConnectorRegistryCreateRequest = {
  key: string
  name: string
  connector_type: ConnectorType
  driver: string
  enabled: boolean
  priority: number
  scope: string
  config_json: Record<string, unknown>
  tags_json: string[]
}

export type ConnectorRegistryPatchRequest = Partial<{
  name: string
  enabled: boolean
  priority: number
  scope: string
  config_json: Record<string, unknown>
  tags_json: string[]
}>

export type SearchSourcePolicy = {
  policy_id: string
  mode: string
  default_connector_key: string
  allow_fallback: boolean
  fallback_connector_keys: string[]
  routing_rules: Record<string, unknown>[]
  updated_at: string
  updated_by: string
}

export type SearchSourcePoliciesResponse = {
  policies: SearchSourcePolicy[]
}

export type SearchSourcePolicyUpsertRequest = {
  mode: string
  default_connector_key: string
  allow_fallback: boolean
  fallback_connector_keys: string[]
  routing_rules: Record<string, unknown>[]
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

  getConnectorRegistry: async () => {
    const response = await apiClient.get('/settings/connector-registry')
    return response.data as ConnectorRegistryListResponse
  },

  createConnectorRegistryItem: async (payload: ConnectorRegistryCreateRequest) => {
    const response = await apiClient.post('/settings/connector-registry', payload)
    return response.data as ConnectorRegistryItem
  },

  patchConnectorRegistryItem: async (connectorId: string, payload: ConnectorRegistryPatchRequest) => {
    const response = await apiClient.patch(`/settings/connector-registry/${connectorId}`, payload)
    return response.data as ConnectorRegistryItem
  },

  reorderConnectorRegistry: async (orderedConnectorIds: string[]) => {
    const response = await apiClient.put('/settings/connector-registry/order', {
      ordered_connector_ids: orderedConnectorIds,
    })
    return response.data as ConnectorRegistryListResponse
  },

  testConnectorRegistryItem: async (connectorId: string) => {
    const response = await apiClient.post(`/settings/connector-registry/${connectorId}/test`)
    return response.data as ConnectorRegistryItem
  },

  getSearchSourcePolicies: async () => {
    const response = await apiClient.get('/settings/search-sources')
    return response.data as SearchSourcePoliciesResponse
  },

  upsertSearchSourcePolicy: async (payload: SearchSourcePolicyUpsertRequest) => {
    const response = await apiClient.put('/settings/search-sources', payload)
    return response.data as SearchSourcePolicy
  },
}
