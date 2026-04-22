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
import { toCanvasUiLabels } from '@/pages/chat-page/config/normalizers'

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

function normalizeBrandingState(payload: BrandingPayload | null | undefined): BrandingState {
  const chatConfig = payload?.ui?.chat
  if (!chatConfig) {
    return DEFAULT_BRANDING_STATE
  }

  const normalizedUiLabels = toCanvasUiLabels(chatConfig.uiLabels)
  return {
    functionType: DEFAULT_FUNCTION_TYPE,
    interactionMode: DEFAULT_INTERACTION_MODE,
    projectSlot: DEFAULT_PROJECT_SLOT,
    uiLabels: {
      ...DEFAULT_CANVAS_UI_LABELS,
      product_name: normalizedUiLabels.product_name,
      brand_tag: normalizedUiLabels.brand_tag,
      project_title: normalizedUiLabels.project_title,
    },
    starterPrompts: DEFAULT_STARTER_PROMPTS,
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
