import { Card, Input, Space, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { PromptTemplateDraft } from './prompt-template-blueprints'

type PromptTemplateDesignerProps = {
  templates: PromptTemplateDraft[]
  editable: boolean
  onChange: (templates: PromptTemplateDraft[]) => void
}

function replaceAt<T>(items: T[], index: number, value: T): T[] {
  return items.map((item, currentIndex) => (currentIndex === index ? value : item))
}

function splitLines(value: string): string[] {
  return value.split('\n').map((item) => item.trim()).filter(Boolean)
}

function TemplateCard(props: {
  template: PromptTemplateDraft
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      className={`settings-prompt-card${props.active ? ' is-active' : ''}`}
      onClick={props.onClick}
      type="button"
    >
      <span>{props.template.stage}</span>
      <strong>{props.template.title}</strong>
      <small>{props.template.dataContractColumns.join(' / ')}</small>
    </button>
  )
}

function TemplateField(props: {
  label: string
  hint: string
  value: string
  editable: boolean
  rows?: number
  onChange: (value: string) => void
}) {
  return (
    <section className="settings-template-field">
      <Typography.Text strong>{props.label}</Typography.Text>
      <Typography.Paragraph className="settings-domain-copy" type="secondary">
        {props.hint}
      </Typography.Paragraph>
      <Input.TextArea
        disabled={!props.editable}
        rows={props.rows || 4}
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
      />
    </section>
  )
}

function PromptTemplateDesigner({ templates, editable, onChange }: PromptTemplateDesignerProps) {
  const [activeKey, setActiveKey] = useState(templates[0]?.key || '')
  const activeIndex = useMemo(
    () => Math.max(0, templates.findIndex((item) => item.key === activeKey)),
    [activeKey, templates],
  )
  const active = templates[activeIndex] || templates[0]

  const updateActive = (patch: Partial<PromptTemplateDraft>) => {
    if (!active) {
      return
    }
    onChange(replaceAt(templates, activeIndex, { ...active, ...patch }))
  }

  if (!active) {
    return null
  }

  return (
    <div className="settings-prompt-designer">
      <div className="settings-prompt-designer__rail">
        <Typography.Text strong>Prompt 模板</Typography.Text>
        <Typography.Paragraph className="settings-domain-copy" type="secondary">
          按阶段准入、字段依赖和交付物口径维护模板。
        </Typography.Paragraph>
        <div className="settings-prompt-card-list">
          {templates.map((template) => (
            <TemplateCard
              key={template.key}
              template={template}
              active={template.key === active.key}
              onClick={() => setActiveKey(template.key)}
            />
          ))}
        </div>
      </div>

      <Card className="settings-prompt-designer__editor" bordered={false}>
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <div className="settings-prompt-title-row">
            <div>
              <Tag color="blue">{active.stage}</Tag>
              {active.dataContractColumns.map((item) => <Tag key={item}>{item}</Tag>)}
            </div>
            <Typography.Text type="secondary">阶段模板</Typography.Text>
          </div>
          <Input disabled={!editable} value={active.title} onChange={(event) => updateActive({ title: event.target.value })} />
          <div className="settings-domain-editor-grid settings-domain-editor-grid--two">
            <TemplateField
              label="输入字段"
              hint="阶段准入与变量绑定所需字段。"
              value={active.inputFields.join('\n')}
              editable={editable}
              onChange={(value) => updateActive({ inputFields: splitLines(value) })}
            />
            <TemplateField
              label="输出结构"
              hint="用于结果校验、工作台投影和归档追溯的输出块。"
              value={active.outputContract.join('\n')}
              editable={editable}
              onChange={(value) => updateActive({ outputContract: splitLines(value) })}
            />
          </div>
          <TemplateField
            label="指令正文"
            hint="定义阶段任务、阻塞条件、输出边界和可追溯要求。"
            rows={7}
            value={active.instruction}
            editable={editable}
            onChange={(value) => updateActive({ instruction: value })}
          />
        </Space>
      </Card>
    </div>
  )
}

export default PromptTemplateDesigner
