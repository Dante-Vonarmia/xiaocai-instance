import { Button, Card, Space, Tabs, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import {
  buildDomainAssetsDraft,
  countDraftFields,
  countCategoryTree,
  type DomainAssetsDraftPayload,
  type DomainAssetsSummary,
  type DomainFieldItem,
  type PromptFallbackTemplate,
  type CategoryOwnerNode,
} from './domain-assets-model'
import { buildPayload, hydrateEditorState, type EditorState } from './domain-assets-editor-model'
import { FieldGroupsEditor, QuestionPolicyEditor } from './DomainAssetsListEditors'
import CategoryEditor from './CategoryTreeEditor'
import PromptTemplateDesigner from './PromptTemplateDesigner'
import type { PromptTemplateDraft } from './prompt-template-blueprints'

type DomainAssetsEditorProps = {
  summary: DomainAssetsSummary
  draftPayload?: Record<string, unknown> | null
  draftUpdatedAt?: string
  saving: boolean
  onSave: (payload: DomainAssetsDraftPayload) => Promise<void> | void
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
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    setState(hydrateEditorState(initialPayload))
    setEditing(false)
  }, [initialPayload])

  const payload = useMemo(() => buildPayload(state), [state])
  const fieldCount = useMemo(() => countDraftFields(payload), [payload])
  const categoryCounts = useMemo(() => countCategoryTree(state.categoryTree), [state.categoryTree])

  const setFields = (groupKey: DomainFieldItem['requiredLevel'], fields: DomainFieldItem[]) => {
    setState((current) => ({ ...current, fields: { ...current.fields, [groupKey]: fields } }))
  }
  const setCategoryTree = (tree: CategoryOwnerNode[]) => updateState(setState, 'categoryTree', tree)
  const setAskOrder = (items: string[]) => updateState(setState, 'askOrder', items)
  const setFallbacks = (items: PromptFallbackTemplate[]) => updateState(setState, 'followupTemplates', items)
  const setAnalysisSections = (items: string[]) => updateState(setState, 'analysisSections', items)
  const setPromptTemplates = (items: PromptTemplateDraft[]) => updateState(setState, 'promptTemplates', items)
  const cancelEditing = () => {
    setState(hydrateEditorState(initialPayload))
    setEditing(false)
  }

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <div className="settings-domain-metrics">
        <Metric label="字段" value={fieldCount} hint="虚拟列表编辑" />
        <Metric label="采购负责类" value={categoryCounts.ownerCount} hint={`一级 ${categoryCounts.level1Count} / 二级 ${categoryCounts.level2Count}`} />
        <Metric label="字段优先级" value={payload.prompts.askOrder.length} hint="追问排序" />
        <Metric label="Prompt模板" value={payload.prompts.promptTemplates?.length || 0} hint="处理阶段" />
      </div>

      <div className="settings-domain-edit-toolbar">
        <Typography.Text type="secondary">{editing ? '编辑中' : '默认只读'}</Typography.Text>
        {!editing ? (
          <Button type="primary" onClick={() => setEditing(true)}>编辑配置</Button>
        ) : null}
      </div>

      <Card className="settings-domain-editor" bordered={false}>
        <Tabs
          items={[
            {
              key: 'fields',
              label: '字段配置',
              children: <FieldGroupsEditor fields={state.fields} editable={editing} onChange={setFields} />,
            },
            {
              key: 'category',
              label: '品类目录',
              children: (
                <CategoryEditor
                  categoryTree={state.categoryTree}
                  editable={editing}
                  onChange={setCategoryTree}
                />
              ),
            },
            {
              key: 'question-policy',
              label: '追问策略',
              children: (
                <QuestionPolicyEditor
                  askOrder={state.askOrder}
                  followupTemplates={state.followupTemplates}
                  analysisSections={state.analysisSections}
                  editable={editing}
                  onAskOrderChange={setAskOrder}
                  onFallbackChange={setFallbacks}
                  onAnalysisSectionsChange={setAnalysisSections}
                />
              ),
            },
            {
              key: 'prompt-templates',
              label: 'Prompt 模板',
              children: (
                <PromptTemplateDesigner
                  templates={state.promptTemplates}
                  editable={editing}
                  onChange={setPromptTemplates}
                />
              ),
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
          {editing ? <Button disabled={saving} onClick={cancelEditing}>取消编辑</Button> : null}
          <Button disabled={!editing} type="primary" loading={saving} onClick={() => onSave(payload)}>保存草稿</Button>
        </Space>
      </div>
    </Space>
  )
}

export default DomainAssetsEditor
