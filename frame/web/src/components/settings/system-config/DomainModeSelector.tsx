import { Card, Radio, Spin, Typography } from 'antd'
import type { DomainInjectionMode } from '@/services/settingsApi'

function DomainModeSelector({
  value,
  loading,
  onChange,
}: {
  value: DomainInjectionMode
  loading: boolean
  onChange: (mode: DomainInjectionMode) => void
}) {
  return (
    <Card title="注入模式" bordered={false}>
      <Typography.Text>Domain 注入模式</Typography.Text>
      <div style={{ marginTop: 12 }}>
        <Radio.Group
          buttonStyle="solid"
          optionType="button"
          options={[
            { label: '关闭', value: 'off' },
            { label: '辅助', value: 'assist' },
            { label: '强制', value: 'enforce' },
          ]}
          value={value}
          onChange={(event) => onChange(event.target.value as DomainInjectionMode)}
        />
        {loading ? <Spin size="small" style={{ marginLeft: 8 }} /> : null}
      </div>
    </Card>
  )
}

export default DomainModeSelector
