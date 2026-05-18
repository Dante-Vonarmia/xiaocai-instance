import { Alert, Empty, Spin, message } from 'antd'
import { useEffect, useState } from 'react'
import { instanceApi } from '@/services/instanceApi'
import { settingsApi, type ConfigDraft } from '@/services/settingsApi'
import DomainAssetsEditor from './DomainAssetsEditor'
import {
  normalizeDomainFields,
  parseCategoryAsset,
  parsePromptAssets,
  type DomainAssetsDraftPayload,
  type DomainAssetsSummary,
} from './domain-assets-model'
import './domain-assets-section.css'

const CATEGORY_ASSET_PATH = 'domain-packs/category-fields/procurement-category-fields.yaml'
const QUESTION_FLOW_PATH = 'domain-packs/activity_procurement/question_flow.yaml'
const ANALYSIS_TEMPLATE_PATH = 'domain-packs/activity_procurement/analysis_template.md'
const CONFIG_KEY = 'procurement_domain_assets'
const CONFIG_SCOPE = 'procurement'

function DomainAssetsSection() {
  const [summary, setSummary] = useState<DomainAssetsSummary | null>(null)
  const [draft, setDraft] = useState<ConfigDraft | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const [fieldsPayload, categoryText, questionFlowText, analysisTemplateText, draftResponse] = await Promise.all([
          instanceApi.getDomainFields('procurement'),
          instanceApi.getDomainPackText(CATEGORY_ASSET_PATH),
          instanceApi.getDomainPackText(QUESTION_FLOW_PATH),
          instanceApi.getDomainPackText(ANALYSIS_TEMPLATE_PATH),
          settingsApi.getConfigDraft(CONFIG_KEY, CONFIG_SCOPE),
        ])
        if (!cancelled) {
          setSummary({
            fields: normalizeDomainFields(fieldsPayload),
            category: parseCategoryAsset(categoryText),
            prompts: parsePromptAssets(questionFlowText, analysisTemplateText),
          })
          setDraft(draftResponse.draft)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '加载领域配置失败')
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

  const saveDraft = async (payload: DomainAssetsDraftPayload) => {
    if (!summary) {
      return
    }
    setSaving(true)
    setError('')
    try {
      const saved = await settingsApi.upsertConfigDraft(CONFIG_KEY, {
        scope: CONFIG_SCOPE,
        base_version: summary.fields.version,
        payload,
      })
      setDraft(saved)
      message.success('配置草稿已保存')
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存配置草稿失败')
    } finally {
      setSaving(false)
    }
  }

  const resetDraft = async () => {
    setSaving(true)
    setError('')
    try {
      await settingsApi.deleteConfigDraft(CONFIG_KEY, CONFIG_SCOPE)
      setDraft(null)
      message.success('已恢复 domain-pack 默认配置')
    } catch (err) {
      setError(err instanceof Error ? err.message : '恢复默认配置失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      {error ? <Alert type="error" showIcon message={error} className="settings-domain-alert" /> : null}
      {loading ? <div className="settings-domain-loading"><Spin /></div> : null}
      {!loading && !summary && !error ? <Empty description="暂无领域配置" /> : null}
      {summary ? (
        <DomainAssetsEditor
          summary={summary}
          draftPayload={draft?.payload}
          draftUpdatedAt={draft?.updated_at}
          saving={saving}
          onSave={saveDraft}
          onReset={resetDraft}
        />
      ) : null}
    </>
  )
}

export default DomainAssetsSection
