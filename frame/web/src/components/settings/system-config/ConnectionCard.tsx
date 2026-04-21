import { Alert, Button, Space, Switch, Tag, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { ConnectorStatus } from '@/services/settingsApi'
import { formatTime, toHealthLabel, toStatusLabel } from './model'

const STATUS_COLOR: Record<string, string> = {
  connected: '#22c55e',
  disconnected: '#9ca3af',
  error: '#ef4444',
}

function ConnectionCard({
  connector,
  title,
  icon,
  loading,
  extraActions,
  onToggleEnabled,
  onTestConnection,
}: {
  connector: ConnectorStatus
  title: string
  icon: ReactNode
  loading: boolean
  extraActions?: ReactNode
  onToggleEnabled: (enabled: boolean) => void
  onTestConnection: () => void
}) {
  return (
    <div className="settings-connector-card">
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <div className="settings-connector-header">
          <Space>
            <span className="settings-connector-icon">{icon}</span>
            <Typography.Text strong>{title}</Typography.Text>
          </Space>
          <Space>
            <span
              className="settings-status-dot"
              style={{ backgroundColor: STATUS_COLOR[connector.status] || '#9ca3af' }}
            />
            <Typography.Text type="secondary">{toStatusLabel(connector.status)}</Typography.Text>
          </Space>
        </div>

        <Space wrap>
          <Tag>健康：{toHealthLabel(connector.health)}</Tag>
          <Tag>延迟：{connector.latency_ms ?? '-'} ms</Tag>
          <Tag>权限：{connector.scope}</Tag>
          <Tag>最近成功：{formatTime(connector.last_success_at)}</Tag>
        </Space>

        {connector.last_error ? <Alert type="error" showIcon message={connector.last_error} /> : null}

        <div className="settings-connector-actions">
          <Space>
            <Switch
              checked={connector.enabled}
              checkedChildren="启用"
              unCheckedChildren="停用"
              loading={loading}
              onChange={(enabled) => onToggleEnabled(enabled)}
            />
            <Button loading={loading} onClick={onTestConnection}>
              测试连接
            </Button>
            {extraActions}
          </Space>
        </div>
      </Space>
    </div>
  )
}

export default ConnectionCard
