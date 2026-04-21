import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { settingsApi, type ConnectorStatus, type DomainInjectionMode } from '@/services/settingsApi'

type SettingsContextValue = {
  domainInjectionMode: DomainInjectionMode
  connectors: ConnectorStatus[]
  loading: boolean
  error: string
  modeUpdating: boolean
  connectorUpdating: Record<string, boolean>
  reload: () => Promise<void>
  updateDomainInjectionMode: (nextMode: DomainInjectionMode) => Promise<void>
  updateConnectorEnabled: (key: string, enabled: boolean) => Promise<void>
  testConnector: (key: string) => Promise<void>
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

function normalizeErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }
  return fallback
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [domainInjectionMode, setDomainInjectionMode] = useState<DomainInjectionMode>('assist')
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modeUpdating, setModeUpdating] = useState(false)
  const [connectorUpdating, setConnectorUpdating] = useState<Record<string, boolean>>({})

  const reload = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await settingsApi.getIntegrations()
      setDomainInjectionMode(payload.domain_injection_mode)
      setConnectors(payload.connectors)
    } catch (err) {
      setError(normalizeErrorMessage(err, '加载连接配置失败'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  const updateDomainInjectionMode = useCallback(async (nextMode: DomainInjectionMode) => {
    setModeUpdating(true)
    setError('')
    try {
      const payload = await settingsApi.setDomainInjectionMode(nextMode)
      setDomainInjectionMode(payload.domain_injection_mode)
      setConnectors(payload.connectors)
    } catch (err) {
      setError(normalizeErrorMessage(err, '更新 domain_injection_mode 失败'))
    } finally {
      setModeUpdating(false)
    }
  }, [])

  const updateConnectorEnabled = useCallback(async (key: string, enabled: boolean) => {
    setConnectorUpdating((prev) => ({ ...prev, [key]: true }))
    setError('')
    try {
      const updated = await settingsApi.setConnectorEnabled(key, enabled)
      setConnectors((prev) => prev.map((item) => (item.key === key ? updated : item)))
    } catch (err) {
      setError(normalizeErrorMessage(err, `更新 connector ${key} 失败`))
    } finally {
      setConnectorUpdating((prev) => ({ ...prev, [key]: false }))
    }
  }, [])

  const testConnector = useCallback(async (key: string) => {
    setConnectorUpdating((prev) => ({ ...prev, [key]: true }))
    setError('')
    try {
      const updated = await settingsApi.testConnector(key)
      setConnectors((prev) => prev.map((item) => (item.key === key ? updated : item)))
    } catch (err) {
      setError(normalizeErrorMessage(err, `测试 connector ${key} 失败`))
    } finally {
      setConnectorUpdating((prev) => ({ ...prev, [key]: false }))
    }
  }, [])

  const value = useMemo<SettingsContextValue>(() => ({
    domainInjectionMode,
    connectors,
    loading,
    error,
    modeUpdating,
    connectorUpdating,
    reload,
    updateDomainInjectionMode,
    updateConnectorEnabled,
    testConnector,
  }), [
    connectorUpdating,
    connectors,
    domainInjectionMode,
    error,
    loading,
    modeUpdating,
    reload,
    testConnector,
    updateConnectorEnabled,
    updateDomainInjectionMode,
  ])

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettingsContext() {
  const context = useContext(SettingsContext)
  if (!context) {
    throw new Error('useSettingsContext must be used within SettingsProvider')
  }
  return context
}
