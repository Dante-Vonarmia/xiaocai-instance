import { ApiOutlined, ArrowDownOutlined, ArrowUpOutlined } from '@ant-design/icons'
import { Button, Card, Empty, Space, Tag } from 'antd'
import type { ConnectorStatus } from '@/services/settingsApi'
import ConnectionCard from './ConnectionCard'
import { isMcpConnector, toConnectorDisplayName } from './model'

function sortByOrder(connectors: ConnectorStatus[], orderedKeys: string[]) {
  const indexMap = new Map(orderedKeys.map((key, index) => [key, index]))
  return [...connectors].sort((a, b) => {
    const aIndex = indexMap.has(a.key) ? indexMap.get(a.key)! : Number.MAX_SAFE_INTEGER
    const bIndex = indexMap.has(b.key) ? indexMap.get(b.key)! : Number.MAX_SAFE_INTEGER
    if (aIndex === bIndex) {
      return a.key.localeCompare(b.key)
    }
    return aIndex - bIndex
  })
}

function McpConnectorSection({
  connectors,
  orderedMcpKeys,
  connectorUpdating,
  onMovePriority,
  onToggleEnabled,
  onTestConnection,
}: {
  connectors: ConnectorStatus[]
  orderedMcpKeys: string[]
  connectorUpdating: Record<string, boolean>
  onMovePriority: (key: string, direction: 'up' | 'down') => void
  onToggleEnabled: (key: string, enabled: boolean) => void
  onTestConnection: (key: string) => void
}) {
  const mcpConnectors = sortByOrder(connectors.filter(isMcpConnector), orderedMcpKeys)

  return (
    <Card title="MCP 连接（可配置优先级）" bordered={false}>
      {mcpConnectors.length === 0 ? <Empty description="暂无 MCP 连接" /> : null}
      {mcpConnectors.length > 0 ? (
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          {mcpConnectors.map((connector, index) => (
            <ConnectionCard
              connector={connector}
              extraActions={(
                <Space>
                  <Tag color="blue">优先级 {index + 1}</Tag>
                  <Button
                    disabled={index === 0}
                    icon={<ArrowUpOutlined />}
                    onClick={() => onMovePriority(connector.key, 'up')}
                    size="small"
                  >
                    上移
                  </Button>
                  <Button
                    disabled={index === mcpConnectors.length - 1}
                    icon={<ArrowDownOutlined />}
                    onClick={() => onMovePriority(connector.key, 'down')}
                    size="small"
                  >
                    下移
                  </Button>
                </Space>
              )}
              icon={<ApiOutlined />}
              key={connector.key}
              loading={connectorUpdating[connector.key] === true}
              onTestConnection={() => onTestConnection(connector.key)}
              onToggleEnabled={(enabled) => onToggleEnabled(connector.key, enabled)}
              title={toConnectorDisplayName(connector)}
            />
          ))}
        </Space>
      ) : null}
    </Card>
  )
}

export default McpConnectorSection
