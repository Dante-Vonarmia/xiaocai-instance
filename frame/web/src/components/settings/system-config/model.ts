import type { ConnectorStatus } from '@/services/settingsApi'

export type SystemBlockKey = 'domain_mode' | 'knowledge_connectors' | 'mcp_connectors'

export const SYSTEM_BLOCK_LABELS: Record<SystemBlockKey, string> = {
  domain_mode: '显示 Domain 注入模式',
  knowledge_connectors: '显示资料库连接',
  mcp_connectors: '显示 MCP 连接',
}

export function isMcpConnector(connector: ConnectorStatus) {
  const key = connector.key.toLowerCase()
  const name = connector.name.toLowerCase()
  return key.includes('mcp') || name.includes('mcp')
}

export function toConnectorDisplayName(connector: ConnectorStatus) {
  const key = connector.key.toLowerCase()
  if (key === 'xiaocai_db') {
    return '小采数据库'
  }
  if (key === 'external_search') {
    return '外部检索'
  }
  if (key === 'mcp_gateway') {
    return 'MCP 网关'
  }
  return connector.name
}

export function toStatusLabel(status: ConnectorStatus['status']) {
  if (status === 'connected') {
    return '已连接'
  }
  if (status === 'error') {
    return '异常'
  }
  return '未连接'
}

export function toHealthLabel(health: string) {
  const normalized = health.trim().toLowerCase()
  if (normalized === 'up') {
    return '正常'
  }
  if (normalized === 'down') {
    return '不可用'
  }
  return health || '-'
}

export function formatTime(value: string | null) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}
