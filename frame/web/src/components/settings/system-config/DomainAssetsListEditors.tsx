import { Button, Input, Space, Tag, Typography } from 'antd'
import { FIELD_GROUPS, type DomainFieldItem, type PromptFallbackTemplate } from './domain-assets-model'
import { FIELD_GROUP_LABELS } from './domain-assets-editor-model'
import VirtualRows from './VirtualRows'

type FieldListEditorProps = {
  groupKey: (typeof FIELD_GROUPS)[number]
  fields: DomainFieldItem[]
  editable: boolean
  onChange: (fields: DomainFieldItem[]) => void
}

type NameListEditorProps = {
  title: string
  hint: string
  items: string[]
  editable: boolean
  onChange: (items: string[]) => void
}

type QuestionPolicyEditorProps = {
  askOrder: string[]
  followupTemplates: PromptFallbackTemplate[]
  analysisSections: string[]
  editable: boolean
  onAskOrderChange: (items: string[]) => void
  onFallbackChange: (items: PromptFallbackTemplate[]) => void
  onAnalysisSectionsChange: (items: string[]) => void
}

function replaceAt<T>(items: T[], index: number, value: T): T[] {
  return items.map((item, currentIndex) => (currentIndex === index ? value : item))
}

function removeAt<T>(items: T[], index: number): T[] {
  return items.filter((_, currentIndex) => currentIndex !== index)
}

function SectionHeader({ title, hint, count }: { title: string; hint: string; count: number }) {
  return (
    <div className="settings-list-header">
      <div>
        <Typography.Text strong>{title}</Typography.Text>
        <Typography.Paragraph className="settings-domain-copy" type="secondary">
          {hint}
        </Typography.Paragraph>
      </div>
      <Tag>{count}</Tag>
    </div>
  )
}

function FieldReadonlyRow({ field }: { field: DomainFieldItem }) {
  return (
    <div className="settings-field-readonly-row">
      <div className="settings-field-readonly-row__main">
        <Typography.Text strong>{field.label || field.key || '未命名字段'}</Typography.Text>
        <Space wrap size={6}>
          <Tag>{field.key || '-'}</Tag>
          <Tag>{field.type || 'string'}</Tag>
        </Space>
      </div>
      <Typography.Paragraph className="settings-domain-copy" type="secondary">
        {field.description || '暂无业务含义 / 数据口径说明'}
      </Typography.Paragraph>
    </div>
  )
}

export function FieldListEditor({ groupKey, fields, editable, onChange }: FieldListEditorProps) {
  const updateField = (index: number, patch: Partial<DomainFieldItem>) => {
    onChange(replaceAt(fields, index, { ...fields[index], ...patch }))
  }

  return (
    <section className="settings-structured-card">
      <SectionHeader
        title={FIELD_GROUP_LABELS[groupKey]}
        hint={editable ? '草稿编辑中' : '默认只读'}
        count={fields.length}
      />
      <VirtualRows
        items={fields}
        height={280}
        rowHeight={editable ? 116 : 88}
        itemKey={(field, index) => `${field.key || field.label || 'field'}-${index}`}
        renderItem={(field, index) => editable ? (
          <div className="settings-field-row">
            <Input value={field.key} placeholder="字段 key" onChange={(event) => updateField(index, { key: event.target.value })} />
            <Input value={field.label} placeholder="中文名" onChange={(event) => updateField(index, { label: event.target.value })} />
            <Input value={field.type} placeholder="类型" onChange={(event) => updateField(index, { type: event.target.value })} />
            <Button danger onClick={() => onChange(removeAt(fields, index))}>删除</Button>
            <Input.TextArea
              value={field.description}
              placeholder="业务含义 / 数据口径 / 示例说明"
              rows={2}
              onChange={(event) => updateField(index, { description: event.target.value })}
            />
          </div>
        ) : <FieldReadonlyRow field={field} />}
      />
      {editable ? (
        <Button onClick={() => onChange([...fields, { key: '', label: '', type: 'string', description: '', requiredLevel: groupKey }])}>
          添加字段
        </Button>
      ) : null}
    </section>
  )
}

export function NameListEditor({ title, hint, items, editable, onChange }: NameListEditorProps) {
  return (
    <section className="settings-structured-card">
      <SectionHeader title={title} hint={hint} count={items.length} />
      <VirtualRows
        items={items}
        height={260}
        rowHeight={58}
        itemKey={(item, index) => `${item || 'name'}-${index}`}
        renderItem={(item, index) => editable ? (
          <div className="settings-name-row">
            <Tag>{index + 1}</Tag>
            <Input value={item} onChange={(event) => onChange(replaceAt(items, index, event.target.value))} />
            <Button danger onClick={() => onChange(removeAt(items, index))}>删除</Button>
          </div>
        ) : (
          <div className="settings-name-readonly-row">
            <Tag>{index + 1}</Tag>
            <Typography.Text>{item || '-'}</Typography.Text>
          </div>
        )}
      />
      {editable ? <Button onClick={() => onChange([...items, ''])}>添加</Button> : null}
    </section>
  )
}

function FallbackRows(props: {
  items: PromptFallbackTemplate[]
  editable: boolean
  onChange: (items: PromptFallbackTemplate[]) => void
}) {
  const updateItem = (index: number, patch: Partial<PromptFallbackTemplate>) => {
    props.onChange(replaceAt(props.items, index, { ...props.items[index], ...patch }))
  }

  return (
    <section className="settings-structured-card">
      <SectionHeader title="参考话术" hint="缺失字段确认的参考表达。" count={props.items.length} />
      <VirtualRows
        items={props.items}
        height={260}
        rowHeight={74}
        itemKey={(item, index) => `${item.key || 'fallback'}-${index}`}
        renderItem={(item, index) => props.editable ? (
          <div className="settings-fallback-row">
            <Input value={item.key} placeholder="字段 key" onChange={(event) => updateItem(index, { key: event.target.value })} />
            <Input value={item.text} placeholder="参考话术" onChange={(event) => updateItem(index, { text: event.target.value })} />
            <Button danger onClick={() => props.onChange(removeAt(props.items, index))}>删除</Button>
          </div>
        ) : (
          <div className="settings-fallback-readonly-row">
            <Tag>{item.key || '-'}</Tag>
            <Typography.Text>{item.text || '-'}</Typography.Text>
          </div>
        )}
      />
      {props.editable ? <Button onClick={() => props.onChange([...props.items, { key: '', text: '' }])}>添加话术</Button> : null}
    </section>
  )
}

export function QuestionPolicyEditor({
  askOrder,
  followupTemplates,
  analysisSections,
  editable,
  onAskOrderChange,
  onFallbackChange,
  onAnalysisSectionsChange,
}: QuestionPolicyEditorProps) {
  return (
    <div className="settings-domain-editor-grid settings-domain-editor-grid--three">
      <NameListEditor
        title="字段优先级"
        hint="缺失字段判断和追问排序。"
        items={askOrder}
        editable={editable}
        onChange={onAskOrderChange}
      />
      <FallbackRows items={followupTemplates} editable={editable} onChange={onFallbackChange} />
      <NameListEditor
        title="分析章节"
        hint="报告章节顺序。"
        items={analysisSections}
        editable={editable}
        onChange={onAnalysisSectionsChange}
      />
    </div>
  )
}

export function FieldGroupsEditor(props: {
  fields: Record<(typeof FIELD_GROUPS)[number], DomainFieldItem[]>
  editable: boolean
  onChange: (groupKey: (typeof FIELD_GROUPS)[number], fields: DomainFieldItem[]) => void
}) {
  return (
    <div className="settings-domain-editor-grid">
      {FIELD_GROUPS.map((groupKey) => (
        <FieldListEditor
          key={groupKey}
          groupKey={groupKey}
          fields={props.fields[groupKey]}
          editable={props.editable}
          onChange={(fields) => props.onChange(groupKey, fields)}
        />
      ))}
    </div>
  )
}
