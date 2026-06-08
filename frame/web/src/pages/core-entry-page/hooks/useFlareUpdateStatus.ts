import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  flareUpdatesApi,
  type FlarePackageStatus,
  type FlareRuntimeGateStatus,
  type FlareUpdateStatusResponse,
} from '@/services/api'

const NPM_PACKAGES = [
  'flare-chat-core',
  'flare-chat-ui',
  'flare-canvas-ui',
  'flare-generative-ui',
] as const

type LoadState = 'checking' | 'ready' | 'error'

export type FlareUpdateSummary = {
  loadState: LoadState
  title: string
  tone: 'neutral' | 'ok' | 'warning' | 'danger'
  updateCount: number
  packages: FlarePackageStatus[]
  runtimeGate?: FlareRuntimeGateStatus
  error?: string
  refresh: () => void
}

function currentWebVersion(packageName: string) {
  return String(__XIAOCAI_FLARE_WEB_VERSIONS__[packageName] || '').trim() || null
}

async function latestNpmVersion(packageName: string) {
  const response = await fetch(`https://registry.npmjs.org/${packageName}/latest`, {
    cache: 'no-store',
  })
  if (!response.ok) {
    return null
  }
  const payload = await response.json() as { version?: unknown }
  return typeof payload.version === 'string' && payload.version.trim()
    ? payload.version.trim()
    : null
}

async function resolveNpmStatuses() {
  return Promise.all(NPM_PACKAGES.map(async (packageName) => {
    const current = currentWebVersion(packageName)
    const latest = await latestNpmVersion(packageName).catch(() => null)
    return {
      registry: 'npm' as const,
      package: packageName,
      current,
      latest,
      source: 'web-build',
      update_available: Boolean(current && latest && current !== latest),
    }
  }))
}

function mergeStatus(apiStatus: FlareUpdateStatusResponse, npmPackages: FlarePackageStatus[]) {
  const packages = [...npmPackages, ...apiStatus.packages]
  const updateCount = packages.filter((item) => item.update_available).length
  const hasUnknown = packages.some((item) => !item.latest)
  const gateFailed = apiStatus.runtime_gate.passed !== true
  return {
    packages,
    updateCount,
    tone: gateFailed ? 'danger' as const : updateCount > 0 ? 'warning' as const : 'ok' as const,
    title: gateFailed
      ? 'FLARE 运行门禁异常'
      : updateCount > 0
        ? `发现 ${updateCount} 个 FLARE 更新`
        : hasUnknown
          ? 'FLARE 更新状态未知'
          : 'FLARE 已对齐',
  }
}

export function useFlareUpdateStatus(): FlareUpdateSummary {
  const [loadState, setLoadState] = useState<LoadState>('checking')
  const [apiStatus, setApiStatus] = useState<FlareUpdateStatusResponse | null>(null)
  const [npmPackages, setNpmPackages] = useState<FlarePackageStatus[]>([])
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const refresh = useCallback(() => {
    setRefreshKey((value) => value + 1)
  }, [])

  useEffect(() => {
    let active = true
    async function loadStatus() {
      setLoadState('checking')
      setError('')
      try {
        const [nextApiStatus, nextNpmPackages] = await Promise.all([
          flareUpdatesApi.status(),
          resolveNpmStatuses(),
        ])
        if (!active) {
          return
        }
        setApiStatus(nextApiStatus)
        setNpmPackages(nextNpmPackages)
        setLoadState('ready')
      } catch (caught) {
        if (!active) {
          return
        }
        setError(caught instanceof Error ? caught.message : 'FLARE 更新检查失败')
        setLoadState('error')
      }
    }
    void loadStatus()
    return () => {
      active = false
    }
  }, [refreshKey])

  return useMemo(() => {
    if (loadState === 'error') {
      return {
        loadState,
        title: 'FLARE 更新检查失败',
        tone: 'danger',
        updateCount: 0,
        packages: [],
        error,
        refresh,
      }
    }
    if (!apiStatus) {
      return {
        loadState,
        title: '正在检查 FLARE 更新',
        tone: 'neutral',
        updateCount: 0,
        packages: npmPackages,
        refresh,
      }
    }
    const merged = mergeStatus(apiStatus, npmPackages)
    return {
      loadState,
      title: merged.title,
      tone: merged.tone,
      updateCount: merged.updateCount,
      packages: merged.packages,
      runtimeGate: apiStatus.runtime_gate,
      refresh,
    }
  }, [apiStatus, error, loadState, npmPackages, refresh])
}
