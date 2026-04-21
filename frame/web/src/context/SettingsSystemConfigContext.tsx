import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ConnectorStatus } from '@/services/settingsApi'
import { isMcpConnector, type SystemBlockKey } from '@/components/settings/system-config/model'

type BlockVisibility = Record<SystemBlockKey, boolean>

type SettingsSystemConfigContextValue = {
  blockVisibility: BlockVisibility
  orderedMcpKeys: string[]
  setBlockVisible: (key: SystemBlockKey, visible: boolean) => void
  moveMcpPriority: (key: string, direction: 'up' | 'down') => void
}

const BLOCK_VISIBILITY_KEY = 'xiaocai-settings-system-visibility'
const MCP_ORDER_KEY = 'xiaocai-settings-mcp-order'

const DEFAULT_BLOCK_VISIBILITY: BlockVisibility = {
  domain_mode: true,
  knowledge_connectors: true,
  mcp_connectors: true,
}

const SettingsSystemConfigContext = createContext<SettingsSystemConfigContextValue | null>(null)

function readStoredVisibility(): BlockVisibility {
  try {
    const raw = localStorage.getItem(BLOCK_VISIBILITY_KEY)
    if (!raw) {
      return DEFAULT_BLOCK_VISIBILITY
    }
    const parsed = JSON.parse(raw) as Partial<BlockVisibility>
    return {
      domain_mode: parsed.domain_mode !== false,
      knowledge_connectors: parsed.knowledge_connectors !== false,
      mcp_connectors: parsed.mcp_connectors !== false,
    }
  } catch {
    return DEFAULT_BLOCK_VISIBILITY
  }
}

function readStoredMcpOrder(): string[] {
  try {
    const raw = localStorage.getItem(MCP_ORDER_KEY)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : []
  } catch {
    return []
  }
}

function alignMcpOrder(existing: string[], mcpKeys: string[]) {
  const used = new Set(mcpKeys)
  const head = existing.filter((key) => used.has(key))
  const remaining = mcpKeys.filter((key) => !head.includes(key))
  return [...head, ...remaining]
}

export function SettingsSystemConfigProvider({
  connectors,
  children,
}: {
  connectors: ConnectorStatus[]
  children: React.ReactNode
}) {
  const [blockVisibility, setBlockVisibility] = useState<BlockVisibility>(() => readStoredVisibility())
  const [orderedMcpKeys, setOrderedMcpKeys] = useState<string[]>(() => readStoredMcpOrder())

  const mcpKeys = useMemo(() => connectors.filter(isMcpConnector).map((item) => item.key), [connectors])

  useEffect(() => {
    setOrderedMcpKeys((prev) => alignMcpOrder(prev, mcpKeys))
  }, [mcpKeys])

  useEffect(() => {
    localStorage.setItem(BLOCK_VISIBILITY_KEY, JSON.stringify(blockVisibility))
  }, [blockVisibility])

  useEffect(() => {
    localStorage.setItem(MCP_ORDER_KEY, JSON.stringify(orderedMcpKeys))
  }, [orderedMcpKeys])

  const value = useMemo<SettingsSystemConfigContextValue>(() => ({
    blockVisibility,
    orderedMcpKeys,
    setBlockVisible: (key, visible) => {
      setBlockVisibility((prev) => ({ ...prev, [key]: visible }))
    },
    moveMcpPriority: (key, direction) => {
      setOrderedMcpKeys((prev) => {
        const next = [...prev]
        const index = next.indexOf(key)
        if (index < 0) {
          return prev
        }
        const target = direction === 'up' ? index - 1 : index + 1
        if (target < 0 || target >= next.length) {
          return prev
        }
        ;[next[index], next[target]] = [next[target], next[index]]
        return next
      })
    },
  }), [blockVisibility, orderedMcpKeys])

  return (
    <SettingsSystemConfigContext.Provider value={value}>
      {children}
    </SettingsSystemConfigContext.Provider>
  )
}

export function useSettingsSystemConfigContext() {
  const context = useContext(SettingsSystemConfigContext)
  if (!context) {
    throw new Error('useSettingsSystemConfigContext must be used within SettingsSystemConfigProvider')
  }
  return context
}
