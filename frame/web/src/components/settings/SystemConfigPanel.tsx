import { Alert, Empty, Space, Spin } from 'antd'
import ComponentVisibilityPanel from '@/components/settings/system-config/ComponentVisibilityPanel'
import DomainModeSelector from '@/components/settings/system-config/DomainModeSelector'
import KnowledgeConnectorSection from '@/components/settings/system-config/KnowledgeConnectorSection'
import McpConnectorSection from '@/components/settings/system-config/McpConnectorSection'
import { useSettingsContext } from '@/context/SettingsContext'
import { SettingsSystemConfigProvider, useSettingsSystemConfigContext } from '@/context/SettingsSystemConfigContext'
import type { DomainInjectionMode } from '@/services/settingsApi'

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
  const { blockVisibility, orderedMcpKeys, moveMcpPriority } = useSettingsSystemConfigContext()

  return (
    <Space direction="vertical" style={{ width: '100%' }} size={16}>
      <ComponentVisibilityPanel />

      {blockVisibility.domain_mode ? (
        <DomainModeSelector
          loading={modeUpdating}
          onChange={(mode: DomainInjectionMode) => {
            void updateDomainInjectionMode(mode)
          }}
          value={domainInjectionMode}
        />
      ) : null}

      {error ? <Alert type="error" showIcon message={error} /> : null}
      {loading ? <Spin /> : null}
      {!loading && connectors.length === 0 ? <Empty description="暂无连接配置" /> : null}

      {!loading && connectors.length > 0 && blockVisibility.knowledge_connectors ? (
        <KnowledgeConnectorSection
          connectorUpdating={connectorUpdating}
          connectors={connectors}
          onTestConnection={(key) => {
            void testConnector(key)
          }}
          onToggleEnabled={(key, enabled) => {
            void updateConnectorEnabled(key, enabled)
          }}
        />
      ) : null}

      {!loading && connectors.length > 0 && blockVisibility.mcp_connectors ? (
        <McpConnectorSection
          connectorUpdating={connectorUpdating}
          connectors={connectors}
          onMovePriority={moveMcpPriority}
          onTestConnection={(key) => {
            void testConnector(key)
          }}
          onToggleEnabled={(key, enabled) => {
            void updateConnectorEnabled(key, enabled)
          }}
          orderedMcpKeys={orderedMcpKeys}
        />
      ) : null}
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
