import { Button, Card, Space, Tabs, Tag, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import {
  buildDomainAssetsDraft,
  countDraftFields,
  type DomainAssetsDraftPayload,
  type DomainAssetsSummary,
  type DomainFieldItem,
  type PromptFallbackTemplate,
} from './domain-assets-model'
import { buildPayload, hydrateEditorState, type EditorState } from './domain-assets-editor-model'
import { CategoryEditor, FieldGroupsEditor, QuestionPolicyEditor } from './DomainAssetsListEditors'
import PromptTemplateDesigner from './PromptTemplateDesigner'
import type { PromptTemplateDraft } from './prompt-template-blueprints'

type DomainAssetsEditorProps = {
  summary: DomainAssetsSummary
  draftPayload?: Record<string, unknown> | null
  draftUpdatedAt?: string
  saving: boolean
  onSave: (payload: DomainAssetsDraftPayload) => void
  onReset: () => void
}

function Metric({ label, value, hint }: { label: string; value: number | string; hint: string }) {
  return (
    <div className="settings-domain-metric">
      <Typography.Text type="secondary">{label}</Typography.Text>
      <strong>{value}</strong>
      <span>{hint}</span>
    </div>
  )
}

function updateState<K extends keyof EditorState>(
  setter: (value: (current: EditorState) => EditorState) => void,
  key: K,
  value: EditorState[K],
) {
  setter((current) => ({ ...current, [key]: value }))
}

function DomainAssetsEditor({
  summary,
  draftPayload,
  draftUpdatedAt,
  saving,
  onSave,
  onReset,
}: DomainAssetsEditorProps) {
  const initialPayload = useMemo(
    () => buildDomainAssetsDraft(summary, draftPayload),
    [draftPayload, summary],
  )
  const [state, setState] = useState<EditorState>(() => hydrateEditorState(initialPayload))
  const [fieldEditing, setFieldEditing] = useState(false)

  useEffect(() => {
    setState(hydrateEditorState(initialPayload))
    setFieldEditing(false)
  }, [initialPayload])

  const payload = useMemo(() => buildPayload(state), [state])
  const fieldCount = useMemo(() => countDraftFields(payload), [payload])

  const setFields = (groupKey: DomainFieldItem['requiredLevel'], fields: DomainFieldItem[]) => {
    setState((current) => ({ ...current, fields: { ...current.fields, [groupKey]: fields } }))
  }
  const setOwnerNames = (items: string[]) => updateState(setState, 'ownerNames', items)
  const setLevel1Names = (items: string[]) => updateState(setState, 'level1Names', items)
  const setAskOrder = (items: string[]) => updateState(setState, 'askOrder', items)
  const setFallbacks = (items: PromptFallbackTemplate[]) => updateState(setState, 'followupTemplates', items)
  const setAnalysisSections = (items: string[]) => updateState(setState, 'analysisSections', items)
  const setPromptTemplates = (items: PromptTemplateDraft[]) => updateState(setState, 'promptTemplates', items)

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <div className="settings-domain-intro">
        <div>
          <Typography.Text strong>采购领域配置草稿</Typography.Text>
          <Typography.Paragraph className="settings-domain-copy" type="secondary">
            字段、品类和追问策略使用结构化配置；真正 Prompt 模板单独对齐数据契约维护。
          </Typography.Paragraph>
        </div>
        <Space wrap>
          <Tag color="purple">{summary.fields.packId} · {summary.fields.version}</Tag>
          {draftUpdatedAt ? <Tag color="blue">已保存草稿</Tag> : <Tag>未保存草稿</Tag>}
        </Space>
      </div>

      <div className="settings-domain-metrics">
        <Metric label="字段" value={fieldCount} hint="虚拟列表编辑" />
        <Metric label="采购负责类" value={payload.category.ownerNames.length} hint="品类入口" />
        <Metric label="字段优先级" value={payload.prompts.askOrder.length} hint="模型追问策略" />
        <Metric label="Prompt模板" value={payload.prompts.promptTemplates?.length || 0} hint="数据契约阶段" />
      </div>

      <Card className="settings-domain-editor" bordered={false}>
        <Tabs
          items={[
            {
              key: 'fields',
              label: '字段配置',
              children: (
                <Space direction="vertical" size={14} style={{ width: '100%' }}>
                  <div className="settings-field-intro">
                    <div>
                      <Typography.Text strong>字段是数据契约，不是提示词</Typography.Text>
                      <Typography.Paragraph className="settings-domain-copy" type="secondary">
                        字段用于需求收集、完整性判断、工作台投影和后续分析输入。默认只读，避免把运行契约当作普通文案误改。
                      </Typography.Paragraph>
                    </div>
                    <Button onClick={() => setFieldEditing((current) => !current)}>
                      {fieldEditing ? '退出字段编辑' : '编辑字段草稿'}
                    </Button>
                  </div>
                  <FieldGroupsEditor fields={state.fields} editable={fieldEditing} onChange={setFields} />
                </Space>
              ),
            },
            {
              key: 'category',
              label: '品类目录',
              children: (
                <CategoryEditor
                  ownerNames={state.ownerNames}
                  level1Names={state.level1Names}
                  onOwnerNamesChange={setOwnerNames}
                  onLevel1NamesChange={setLevel1Names}
                />
              ),
            },
            {
              key: 'question-policy',
              label: '模型追问策略',
              children: (
                <QuestionPolicyEditor
                  askOrder={state.askOrder}
                  followupTemplates={state.followupTemplates}
                  analysisSections={state.analysisSections}
                  onAskOrderChange={setAskOrder}
                  onFallbackChange={setFallbacks}
                  onAnalysisSectionsChange={setAnalysisSections}
                />
              ),
            },
            {
              key: 'prompt-templates',
              label: 'Prompt 模板',
              children: <PromptTemplateDesigner templates={state.promptTemplates} onChange={setPromptTemplates} />,
            },
          ]}
        />
      </Card>

      <div className="settings-domain-actions">
        {draftUpdatedAt ? (
          <Typography.Text type="secondary">上次保存：{draftUpdatedAt}</Typography.Text>
        ) : <span />}
        <Space wrap>
          <Button disabled={saving || !draftUpdatedAt} onClick={onReset}>恢复默认</Button>
          <Button type="primary" loading={saving} onClick={() => onSave(payload)}>保存配置草稿</Button>
        </Space>
      </div>
    </Space>
  )
}

export default DomainAssetsEditor
