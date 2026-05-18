import { Card, Input, Space, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { PromptTemplateDraft } from './prompt-template-blueprints'

type PromptTemplateDesignerProps = {
  templates: PromptTemplateDraft[]
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
        rows={props.rows || 4}
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
      />
    </section>
  )
}

function PromptTemplateDesigner({ templates, onChange }: PromptTemplateDesignerProps) {
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
          对齐 Excel 数据契约中的处理阶段，不再和追问策略混在一起。
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
              <Tag color="purple">{active.stage}</Tag>
              {active.dataContractColumns.map((item) => <Tag key={item}>{item}</Tag>)}
            </div>
            <Typography.Text type="secondary">数据契约模板</Typography.Text>
          </div>
          <Input value={active.title} onChange={(event) => updateActive({ title: event.target.value })} />
          <div className="settings-domain-editor-grid settings-domain-editor-grid--two">
            <TemplateField
              label="输入字段契约"
              hint="每行一个输入字段，来自总字段表和品类维度契约。"
              value={active.inputFields.join('\n')}
              onChange={(value) => updateActive({ inputFields: splitLines(value) })}
            />
            <TemplateField
              label="输出结构契约"
              hint="每行一个输出块，作为模型输出校验和 workbench 投影依据。"
              value={active.outputContract.join('\n')}
              onChange={(value) => updateActive({ outputContract: splitLines(value) })}
            />
          </div>
          <TemplateField
            label="模板指令正文"
            hint="这里才是真正的 Prompt 模板。要求模型基于上下文生成问题/结果，不重复询问已确认字段。"
            rows={7}
            value={active.instruction}
            onChange={(value) => updateActive({ instruction: value })}
          />
        </Space>
      </Card>
    </div>
  )
}

export default PromptTemplateDesigner
