import { ApiOutlined, DatabaseOutlined, PlusOutlined, SaveOutlined, SearchOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Empty, Form, Input, InputNumber, Modal, Select, Space, Spin, Switch, Tag, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { settingsApi, type ConnectorRegistryCreateRequest, type ConnectorRegistryItem, type ConnectorType } from '@/services/settingsApi'
import { formatTime, toConnectorDisplayName, toHealthLabel, toStatusLabel } from './model'

function iconByType(type: ConnectorType) {
  if (type === 'database') {
    return <DatabaseOutlined />
  }
  if (type === 'search') {
    return <SearchOutlined />
  }
  return <ApiOutlined />
}

function ConnectorRegistrySection() {
  const [items, setItems] = useState<ConnectorRegistryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingKeys, setUpdatingKeys] = useState<Record<string, boolean>>({})
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm<ConnectorRegistryCreateRequest>()

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await settingsApi.getConnectorRegistry()
      setItems([...payload.connectors].sort((a, b) => a.priority - b.priority))
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据源配置失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const orderedItems = useMemo(
    () => [...items].sort((a, b) => a.priority - b.priority),
    [items],
  )

  const markBusy = (key: string, value: boolean) => {
    setUpdatingKeys((prev) => ({ ...prev, [key]: value }))
  }

  const updateItem = async (connectorId: string, payload: Parameters<typeof settingsApi.patchConnectorRegistryItem>[1], busyKey: string) => {
    markBusy(busyKey, true)
    setError('')
    try {
      const updated = await settingsApi.patchConnectorRegistryItem(connectorId, payload)
      setItems((prev) => prev.map((item) => (item.connector_id === connectorId ? updated : item)))
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新数据源失败')
    } finally {
      markBusy(busyKey, false)
    }
  }

  const testItem = async (connectorId: string, busyKey: string) => {
    markBusy(busyKey, true)
    setError('')
    try {
      const updated = await settingsApi.testConnectorRegistryItem(connectorId)
      setItems((prev) => prev.map((item) => (item.connector_id === connectorId ? updated : item)))
    } catch (err) {
      setError(err instanceof Error ? err.message : '测试连接失败')
    } finally {
      markBusy(busyKey, false)
    }
  }

  const movePriority = async (connectorId: string, direction: 'up' | 'down') => {
    const currentIndex = orderedItems.findIndex((item) => item.connector_id === connectorId)
    if (currentIndex < 0) {
      return
    }
    const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1
    if (targetIndex < 0 || targetIndex >= orderedItems.length) {
      return
    }
    const next = [...orderedItems]
    ;[next[currentIndex], next[targetIndex]] = [next[targetIndex], next[currentIndex]]
    setLoading(true)
    setError('')
    try {
      const payload = await settingsApi.reorderConnectorRegistry(next.map((item) => item.connector_id))
      setItems(payload.connectors)
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新优先级失败')
    } finally {
      setLoading(false)
    }
  }

  const submitCreate = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      setError('')
      const created = await settingsApi.createConnectorRegistryItem(values)
      setItems((prev) => [...prev, created].sort((a, b) => a.priority - b.priority))
      setCreateOpen(false)
      form.resetFields()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card
      title="数据源管理"
      bordered={false}
      extra={(
        <Button
          icon={<PlusOutlined />}
          type="primary"
          onClick={() => {
            setCreateOpen(true)
            form.setFieldsValue({
              connector_type: 'mcp',
              enabled: true,
              priority: (orderedItems.length + 1) * 10,
              scope: 'read',
              config_json: {},
              tags_json: [],
            })
          }}
        >
          新增数据源
        </Button>
      )}
    >
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 12 }} /> : null}
      {loading ? <Spin /> : null}
      {!loading && orderedItems.length === 0 ? <Empty description="暂无数据源配置" /> : null}
      {!loading && orderedItems.length > 0 ? (
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          {orderedItems.map((item, index) => (
            <div className="settings-connector-card" key={item.connector_id}>
              <Space direction="vertical" size={10} style={{ width: '100%' }}>
                <div className="settings-connector-header">
                  <Space>
                    <span className="settings-connector-icon">{iconByType(item.connector_type)}</span>
                    <Typography.Text strong>{toConnectorDisplayName(item)}</Typography.Text>
                    <Tag color="blue">{item.connector_type}</Tag>
                    <Tag>{item.driver}</Tag>
                  </Space>
                  <Space>
                    <span
                      className="settings-status-dot"
                      style={{ backgroundColor: item.status === 'connected' ? '#22c55e' : item.status === 'error' ? '#ef4444' : '#9ca3af' }}
                    />
                    <Typography.Text type="secondary">{toStatusLabel(item.status)}</Typography.Text>
                  </Space>
                </div>

                <Space wrap>
                  <Tag>优先级：{index + 1}</Tag>
                  <Tag>健康：{toHealthLabel(item.health)}</Tag>
                  <Tag>延迟：{item.latency_ms ?? '-'} ms</Tag>
                  <Tag>权限：{item.scope}</Tag>
                  <Tag>最近成功：{formatTime(item.last_success_at)}</Tag>
                </Space>

                {item.last_error ? <Alert type="error" showIcon message={item.last_error} /> : null}

                <Space wrap>
                  <Switch
                    checked={item.enabled}
                    checkedChildren="启用"
                    unCheckedChildren="停用"
                    loading={updatingKeys[item.connector_id] === true}
                    onChange={(enabled) => {
                      void updateItem(item.connector_id, { enabled }, item.connector_id)
                    }}
                  />
                  <Button
                    loading={updatingKeys[item.connector_id] === true}
                    onClick={() => {
                      void testItem(item.connector_id, item.connector_id)
                    }}
                  >
                    测试连接
                  </Button>
                  <Button disabled={index === 0} onClick={() => { void movePriority(item.connector_id, 'up') }}>
                    上移
                  </Button>
                  <Button disabled={index === orderedItems.length - 1} onClick={() => { void movePriority(item.connector_id, 'down') }}>
                    下移
                  </Button>
                </Space>
              </Space>
            </div>
          ))}
        </Space>
      ) : null}

      <Modal
        destroyOnClose
        open={createOpen}
        title="新增数据源"
        onCancel={() => setCreateOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setCreateOpen(false)}>
            取消
          </Button>,
          <Button key="save" icon={<SaveOutlined />} type="primary" onClick={() => { void submitCreate() }}>
            保存
          </Button>,
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="标识 Key" name="key" rules={[{ required: true, message: '请输入 key' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="类型" name="connector_type" rules={[{ required: true, message: '请选择类型' }]}>
            <Select
              options={[
                { label: 'MCP 服务', value: 'mcp' },
                { label: '检索 Search', value: 'search' },
                { label: '数据库 Database', value: 'database' },
                { label: '知识库 Knowledge', value: 'knowledge' },
              ]}
            />
          </Form.Item>
          <Form.Item label="驱动 Driver" name="driver" rules={[{ required: true, message: '请输入 driver' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="优先级" name="priority" rules={[{ required: true, message: '请输入优先级' }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="权限" name="scope">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default ConnectorRegistrySection
