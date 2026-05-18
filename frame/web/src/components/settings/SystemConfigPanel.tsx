import { Alert, Collapse, Empty, Space, Spin, Typography } from 'antd'
import type { CollapseProps } from 'antd'
import { useCallback, useMemo } from 'react'
import ConnectorRegistrySection from '@/components/settings/system-config/ConnectorRegistrySection'
import DomainAssetsSection from '@/components/settings/system-config/DomainAssetsSection'
import DomainModeSelector from '@/components/settings/system-config/DomainModeSelector'
import KnowledgeConnectorSection from '@/components/settings/system-config/KnowledgeConnectorSection'
import McpConnectorSection from '@/components/settings/system-config/McpConnectorSection'
import SearchSourceSection from '@/components/settings/system-config/SearchSourceSection'
import { useSettingsContext } from '@/context/SettingsContext'
import { SettingsSystemConfigProvider, useSettingsSystemConfigContext } from '@/context/SettingsSystemConfigContext'
import type { DomainInjectionMode } from '@/services/settingsApi'
import './system-config-panel.css'

function SystemConfigPanelContent() {
  const {
    connectors,
    domainInjectionMode,
    loading,
    error,
    modeUpdating,
    connectorUpdating,
    updateDomainInjectionMode,
    updateConnectorEnabled,
    testConnector,
  } = useSettingsContext()
  const { orderedMcpKeys, moveMcpPriority } = useSettingsSystemConfigContext()
  const handleDomainModeChange = useCallback((mode: DomainInjectionMode) => {
    void updateDomainInjectionMode(mode)
  }, [updateDomainInjectionMode])
  const handleToggleEnabled = useCallback((key: string, enabled: boolean) => {
    void updateConnectorEnabled(key, enabled)
  }, [updateConnectorEnabled])
  const handleTestConnection = useCallback((key: string) => {
    void testConnector(key)
  }, [testConnector])
  const handleMovePriority = useCallback((key: string, direction: 'up' | 'down') => {
    moveMcpPriority(key, direction)
  }, [moveMcpPriority])
  const items = useMemo<CollapseProps['items']>(() => [
    {
      key: 'basic',
      label: <span className="settings-system-section-label">常用设置</span>,
      showArrow: false,
      children: (
        <DomainModeSelector
          loading={modeUpdating}
          onChange={handleDomainModeChange}
          value={domainInjectionMode}
        />
      ),
    },
    {
      key: 'connections',
      label: <span className="settings-system-section-label">连接状态</span>,
      showArrow: false,
      children: loading ? <Spin /> : (
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          {connectors.length === 0 ? <Empty description="暂无连接配置" /> : null}
          {connectors.length > 0 ? (
            <KnowledgeConnectorSection
              connectorUpdating={connectorUpdating}
              connectors={connectors}
              onTestConnection={handleTestConnection}
              onToggleEnabled={handleToggleEnabled}
            />
          ) : null}
          {connectors.length > 0 ? (
            <McpConnectorSection
              connectorUpdating={connectorUpdating}
              connectors={connectors}
              onMovePriority={handleMovePriority}
              onTestConnection={handleTestConnection}
              onToggleEnabled={handleToggleEnabled}
              orderedMcpKeys={orderedMcpKeys}
            />
          ) : null}
        </Space>
      ),
    },
    {
      key: 'domain-assets',
      label: <span className="settings-system-section-label">字段 / 品类 / 提示词</span>,
      showArrow: false,
      children: <DomainAssetsSection />,
    },
    {
      key: 'sourcing',
      label: <span className="settings-system-section-label">寻源策略</span>,
      showArrow: false,
      children: loading ? <Spin /> : <SearchSourceSection />,
    },
    {
      key: 'advanced',
      label: <span className="settings-system-section-label">高级管理</span>,
      showArrow: false,
      children: loading ? <Spin /> : (
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          <ConnectorRegistrySection />
        </Space>
      ),
    },
  ], [
    connectorUpdating,
    connectors,
    domainInjectionMode,
    handleDomainModeChange,
    handleMovePriority,
    handleTestConnection,
    handleToggleEnabled,
    loading,
    modeUpdating,
    orderedMcpKeys,
  ])

  return (
    <Space direction="vertical" style={{ width: '100%' }} size={16}>
      <Space direction="vertical" size={4}>
        <Typography.Title level={4} style={{ margin: 0 }}>系统设置</Typography.Title>
        <Typography.Text type="secondary">常用项放在前面，连接和高级配置按需展开。</Typography.Text>
      </Space>

      {error ? <Alert type="error" showIcon message={error} /> : null}

      <Collapse
        bordered={false}
        className="settings-system-collapse"
        defaultActiveKey={['basic', 'domain-assets']}
        items={items}
      />
    </Space>
  )
}

function SystemConfigPanel() {
  const { connectors } = useSettingsContext()

  return (
    <SettingsSystemConfigProvider connectors={connectors}>
      <SystemConfigPanelContent />
    </SettingsSystemConfigProvider>
  )
}

export default SystemConfigPanel
