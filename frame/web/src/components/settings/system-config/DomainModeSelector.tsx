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
    <Card title="采购知识规则" bordered={false}>
      <Typography.Text>控制采购场景规则参与对话的强度。</Typography.Text>
      <div style={{ marginTop: 12 }}>
        <Radio.Group
          buttonStyle="solid"
          optionType="button"
          options={[
            { label: '不启用', value: 'off' },
            { label: '辅助建议', value: 'assist' },
            { label: '严格执行', value: 'enforce' },
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
