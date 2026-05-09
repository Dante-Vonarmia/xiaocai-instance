import { Alert, Button, Card, Empty, Select, Space, Spin, Switch, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { settingsApi, type ConnectorRegistryItem, type SearchSourcePolicy } from '@/services/settingsApi'
import { toConnectorDisplayName } from './model'

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

  const savePolicy = async () => {
    setSaving(true)
    setError('')
    try {
      const updated = await settingsApi.upsertSearchSourcePolicy({
        mode: TARGET_MODE,
        default_connector_key: defaultConnectorKey,
        allow_fallback: allowFallback,
        fallback_connector_keys: fallbackConnectorKeys.filter((key) => key !== defaultConnectorKey),
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
    <Card title="寻源策略" bordered={false}>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 12 }} /> : null}
      {loading ? <Spin /> : null}
      {!loading && availableConnectors.length === 0 ? <Empty description="暂无可用数据源" /> : null}
      {!loading && availableConnectors.length > 0 ? (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Typography.Text strong>默认搜索源</Typography.Text>
            <Select
              options={connectorOptions}
              placeholder="请选择默认搜索源"
              style={{ display: 'block', marginTop: 8 }}
              value={defaultConnectorKey || undefined}
              onChange={(value) => {
                setDefaultConnectorKey(value)
                setFallbackConnectorKeys((prev) => prev.filter((item) => item !== value))
              }}
            />
          </div>

          <div className="settings-visibility-item">
            <Typography.Text strong>允许备用源</Typography.Text>
            <Switch
              checked={allowFallback}
              checkedChildren="允许"
              unCheckedChildren="关闭"
              onChange={setAllowFallback}
            />
          </div>

          <div>
            <Typography.Text strong>备用搜索源</Typography.Text>
            <Select
              disabled={!allowFallback}
              mode="multiple"
              options={connectorOptions.filter((item) => item.value !== defaultConnectorKey)}
              placeholder="请选择 fallback 搜索源"
              style={{ display: 'block', marginTop: 8 }}
              value={fallbackConnectorKeys}
              onChange={setFallbackConnectorKeys}
            />
          </div>

          <Space direction="vertical" size={4}>
            <Typography.Text type="secondary">
              适用场景：智能寻源
            </Typography.Text>
            <Typography.Text type="secondary">
              当前仅配置默认源和备用源，详细路由规则沿用后端配置。
            </Typography.Text>
          </Space>

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
        </Space>
      ) : null}
    </Card>
  )
}

export default SearchSourceSection
