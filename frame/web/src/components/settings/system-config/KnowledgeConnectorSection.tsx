import { DatabaseOutlined, SearchOutlined } from '@ant-design/icons'
import { Card, Empty, Space } from 'antd'
import type { ConnectorStatus } from '@/services/settingsApi'
import ConnectionCard from './ConnectionCard'
import { isMcpConnector, toConnectorDisplayName } from './model'

function iconByKey(key: string) {
  if (key === 'xiaocai_db') {
    return <DatabaseOutlined />
  }
  return <SearchOutlined />
}

function KnowledgeConnectorSection({
  connectors,
  connectorUpdating,
  onToggleEnabled,
  onTestConnection,
}: {
  connectors: ConnectorStatus[]
  connectorUpdating: Record<string, boolean>
  onToggleEnabled: (key: string, enabled: boolean) => void
  onTestConnection: (key: string) => void
}) {
  const knowledgeConnectors = connectors.filter((item) => !isMcpConnector(item))

  return (
    <Card title="资料库连接" bordered={false}>
      {knowledgeConnectors.length === 0 ? <Empty description="暂无资料库连接" /> : null}
      {knowledgeConnectors.length > 0 ? (
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          {knowledgeConnectors.map((connector) => (
            <ConnectionCard
              connector={connector}
              icon={iconByKey(connector.key)}
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

export default KnowledgeConnectorSection
