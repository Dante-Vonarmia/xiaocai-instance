import { Alert, Button, Card, Empty, Select, Space, Spin, Switch, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { settingsApi, type ConnectorRegistryItem, type SearchSourcePolicy } from '@/services/settingsApi'
import { toConnectorDisplayName } from './model'
import './search-source-section.css'

const TARGET_MODE = 'intelligent_sourcing'

function SearchSourceSection() {
  const [connectors, setConnectors] = useState<ConnectorRegistryItem[]>([])
  const [policy, setPolicy] = useState<SearchSourcePolicy | null>(null)
  const [defaultConnectorKey, setDefaultConnectorKey] = useState('')
  const [allowFallback, setAllowFallback] = useState(true)
  const [fallbackConnectorKeys, setFallbackConnectorKeys] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const [registryPayload, policyPayload] = await Promise.all([
          settingsApi.getConnectorRegistry(),
          settingsApi.getSearchSourcePolicies(),
        ])
        if (cancelled) {
          return
        }
        const orderedConnectors = [...registryPayload.connectors].sort((a, b) => a.priority - b.priority)
        const targetPolicy = policyPayload.policies.find((item) => item.mode === TARGET_MODE) || null
        setConnectors(orderedConnectors)
        setPolicy(targetPolicy)
        setDefaultConnectorKey(targetPolicy?.default_connector_key || '')
        setAllowFallback(targetPolicy?.allow_fallback ?? true)
        setFallbackConnectorKeys(targetPolicy?.fallback_connector_keys ?? [])
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '加载寻源策略失败')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const availableConnectors = useMemo(
    () => connectors.filter((item) => item.enabled),
    [connectors],
  )

  const connectorOptions = useMemo(
    () => availableConnectors.map((item) => ({
      label: `${toConnectorDisplayName(item)} · ${item.connector_type}`,
      value: item.key,
    })),
    [availableConnectors],
  )
  const selectedDefaultConnector = useMemo(
    () => availableConnectors.find((item) => item.key === defaultConnectorKey) || null,
    [availableConnectors, defaultConnectorKey],
  )
  const selectedFallbackKeys = useMemo(
    () => fallbackConnectorKeys.filter((key) => key !== defaultConnectorKey),
    [defaultConnectorKey, fallbackConnectorKeys],
  )
  const selectedFallbackConnectors = useMemo(
    () => selectedFallbackKeys
      .map((key) => availableConnectors.find((item) => item.key === key))
      .filter((item): item is ConnectorRegistryItem => item !== undefined),
    [availableConnectors, selectedFallbackKeys],
  )
  const fallbackConnectorOptions = useMemo(
    () => connectorOptions.filter((item) => item.value !== defaultConnectorKey),
    [connectorOptions, defaultConnectorKey],
  )

  const savePolicy = async () => {
    setSaving(true)
    setError('')
    try {
      const updated = await settingsApi.upsertSearchSourcePolicy({
        mode: TARGET_MODE,
        default_connector_key: defaultConnectorKey,
        allow_fallback: allowFallback,
        fallback_connector_keys: selectedFallbackKeys,
        routing_rules: policy?.routing_rules ?? [],
      })
      setPolicy(updated)
      setDefaultConnectorKey(updated.default_connector_key)
      setAllowFallback(updated.allow_fallback)
      setFallbackConnectorKeys(updated.fallback_connector_keys)
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存寻源策略失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card
      className="settings-source-card"
      title={(
        <div className="settings-source-title">
          <Typography.Text strong>寻源策略</Typography.Text>
          <Typography.Text className="settings-source-title__meta" type="secondary">
            智能寻源的数据源调度
          </Typography.Text>
        </div>
      )}
      bordered={false}
    >
      {error ? <Alert type="error" showIcon message={error} className="settings-source-alert" /> : null}
      {loading ? <div className="settings-source-loading"><Spin /></div> : null}
      {!loading && availableConnectors.length === 0 ? <Empty description="暂无可用数据源" /> : null}
      {!loading && availableConnectors.length > 0 ? (
        <Space direction="vertical" size={18} className="settings-source-layout">
          <div className="settings-source-intro">
            <div>
              <Typography.Text strong>搜索顺序</Typography.Text>
              <Typography.Paragraph type="secondary" className="settings-source-copy">
                默认源优先执行；开启备用源后，主源不可用或覆盖不足时再补充检索。
              </Typography.Paragraph>
            </div>
            <span className={allowFallback ? 'settings-source-badge is-on' : 'settings-source-badge'}>
              {allowFallback ? '备用源已启用' : '仅使用默认源'}
            </span>
          </div>

          <div className="settings-source-grid">
            <section className="settings-source-pane settings-source-pane--primary">
              <div className="settings-source-pane__header">
                <Typography.Text strong>默认搜索源</Typography.Text>
                <Typography.Text type="secondary">主链路</Typography.Text>
              </div>
              <Select
                className="settings-source-select"
                options={connectorOptions}
                placeholder="请选择默认搜索源"
                suffixIcon={null}
                value={defaultConnectorKey || undefined}
                onChange={(value) => {
                  setDefaultConnectorKey(value)
                  setFallbackConnectorKeys((prev) => prev.filter((item) => item !== value))
                }}
              />
              <div className="settings-source-summary">
                <span className="settings-source-step">1</span>
                <div>
                  <Typography.Text strong>
                    {selectedDefaultConnector ? toConnectorDisplayName(selectedDefaultConnector) : '未选择主源'}
                  </Typography.Text>
                  <Typography.Paragraph type="secondary" className="settings-source-copy">
                    主源承担第一轮供应商、资料库或外部检索命中。
                  </Typography.Paragraph>
                </div>
              </div>
            </section>

            <section className="settings-source-pane">
              <div className="settings-source-toggle">
                <div>
                  <Typography.Text strong>备用搜索源</Typography.Text>
                  <Typography.Paragraph type="secondary" className="settings-source-copy">
                    开启后按优先级补充主源结果。
                  </Typography.Paragraph>
                </div>
                <Switch
                  checked={allowFallback}
                  checkedChildren="允许"
                  unCheckedChildren="关闭"
                  onChange={setAllowFallback}
                />
              </div>
              <Select
                className="settings-source-select"
                disabled={!allowFallback}
                mode="multiple"
                options={fallbackConnectorOptions}
                placeholder="请选择备用搜索源"
                suffixIcon={null}
                value={selectedFallbackKeys}
                onChange={setFallbackConnectorKeys}
              />
              <div className="settings-source-chip-list">
                {selectedFallbackConnectors.length === 0 ? (
                  <Typography.Text type="secondary">未配置备用源</Typography.Text>
                ) : selectedFallbackConnectors.map((item, index) => (
                  <span className="settings-source-chip" key={item.key}>
                    {index + 2}. {toConnectorDisplayName(item)}
                  </span>
                ))}
              </div>
            </section>
          </div>

          <div className="settings-source-actions">
            <div>
              <Typography.Text type="secondary">适用场景：智能寻源</Typography.Text>
              <Typography.Paragraph type="secondary" className="settings-source-copy">
                当前仅配置默认源和备用源，详细路由规则沿用后端配置。
              </Typography.Paragraph>
            </div>
            <Button
              disabled={!defaultConnectorKey}
              loading={saving}
              type="primary"
              onClick={() => {
                void savePolicy()
              }}
            >
              保存策略
            </Button>
          </div>
        </Space>
      ) : null}
    </Card>
  )
}

export default SearchSourceSection
