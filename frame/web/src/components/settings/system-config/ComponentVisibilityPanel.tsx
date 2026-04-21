import { Card, Space, Switch, Typography } from 'antd'
import { useSettingsSystemConfigContext } from '@/context/SettingsSystemConfigContext'
import { SYSTEM_BLOCK_LABELS, type SystemBlockKey } from './model'

const BLOCK_KEYS: SystemBlockKey[] = ['domain_mode', 'knowledge_connectors', 'mcp_connectors']

function ComponentVisibilityPanel() {
  const { blockVisibility, setBlockVisible } = useSettingsSystemConfigContext()

  return (
    <Card title="页面组件配置" bordered={false}>
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {BLOCK_KEYS.map((blockKey) => (
          <div className="settings-visibility-item" key={blockKey}>
            <Typography.Text>{SYSTEM_BLOCK_LABELS[blockKey]}</Typography.Text>
            <Switch
              checked={blockVisibility[blockKey]}
              checkedChildren="显示"
              unCheckedChildren="隐藏"
              onChange={(visible) => setBlockVisible(blockKey, visible)}
            />
          </div>
        ))}
      </Space>
    </Card>
  )
}

export default ComponentVisibilityPanel
