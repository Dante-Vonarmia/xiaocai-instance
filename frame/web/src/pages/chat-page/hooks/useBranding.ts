import { useEffect, useState } from 'react'

import {
  DEFAULT_CANVAS_UI_LABELS,
  DEFAULT_FUNCTION_TYPE,
  DEFAULT_INTERACTION_MODE,
  DEFAULT_PROJECT_SLOT,
  DEFAULT_STARTER_PROMPTS,
  type CanvasUiLabels,
  type InteractionMode,
  type ProjectSlot,
  type StarterPrompt,
} from '@/pages/chat-page/config/constants'
import { isObject, toCanvasUiLabels, toStarterPrompts, toText } from '@/pages/chat-page/config/normalizers'

type BrandingState = {
  functionType: string
  interactionMode: InteractionMode
  projectSlot: ProjectSlot
  uiLabels: CanvasUiLabels
  starterPrompts: StarterPrompt[]
}

type BrandingPayload = {
  ui?: {
    chat?: {
      functionType?: unknown
      defaultInteractionMode?: unknown
      projectSlot?: unknown
      uiLabels?: unknown
      starterPrompts?: unknown[]
    }
  }
}

const DEFAULT_BRANDING_STATE: BrandingState = {
  functionType: DEFAULT_FUNCTION_TYPE,
  interactionMode: DEFAULT_INTERACTION_MODE,
  projectSlot: DEFAULT_PROJECT_SLOT,
  uiLabels: DEFAULT_CANVAS_UI_LABELS,
  starterPrompts: DEFAULT_STARTER_PROMPTS,
}

function normalizeInteractionMode(value: unknown): InteractionMode {
  const mode = toText(value)
  if (mode === 'auto' || mode === 'requirement_canvas' || mode === 'intelligent_sourcing') {
    return mode
  }
  return DEFAULT_INTERACTION_MODE
}

function normalizeProjectSlot(value: unknown): ProjectSlot {
  if (!isObject(value)) {
    return DEFAULT_PROJECT_SLOT
  }
  const projectId = toText(value.project_id) || DEFAULT_PROJECT_SLOT.project_id
  return {
    key: toText(value.key) || projectId,
    project_id: projectId,
    subtitle: toText(value.subtitle) || DEFAULT_PROJECT_SLOT.subtitle,
    name: toText(value.name) || DEFAULT_PROJECT_SLOT.name,
  }
}

function normalizeBrandingState(payload: BrandingPayload | null | undefined): BrandingState {
  const chatConfig = payload?.ui?.chat
  if (!chatConfig) {
    return DEFAULT_BRANDING_STATE
  }

  const starterPrompts = toStarterPrompts(chatConfig.starterPrompts)
  return {
    functionType: toText(chatConfig.functionType) || DEFAULT_FUNCTION_TYPE,
    interactionMode: normalizeInteractionMode(chatConfig.defaultInteractionMode),
    projectSlot: normalizeProjectSlot(chatConfig.projectSlot),
    uiLabels: toCanvasUiLabels(chatConfig.uiLabels),
    starterPrompts: starterPrompts.length > 0 ? starterPrompts : DEFAULT_STARTER_PROMPTS,
  }
}

export function useBranding() {
  const [branding, setBranding] = useState<BrandingState>(DEFAULT_BRANDING_STATE)

  useEffect(() => {
    let cancelled = false

    const loadBranding = async () => {
      try {
        const response = await fetch('/domain-packs/branding/instance-branding.json', { cache: 'no-store' })
        if (!response.ok || cancelled) {
          return
        }
        const payload = await response.json() as BrandingPayload
        if (!cancelled) {
          setBranding(normalizeBrandingState(payload))
        }
      } catch {
        if (!cancelled) {
          setBranding(DEFAULT_BRANDING_STATE)
        }
      }
    }

    void loadBranding()
    return () => {
      cancelled = true
    }
  }, [])

  return branding
}
