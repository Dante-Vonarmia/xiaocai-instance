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
} from '@/constants/chat'
import { isObject, toCanvasUiLabels, toStarterPrompts, toText } from '@/hooks/chat/normalizers'

type BrandingState = {
  functionType: string
  interactionMode: InteractionMode
  projectSlot: ProjectSlot
  uiLabels: CanvasUiLabels
  starterPrompts: StarterPrompt[]
}

type BrandingPayload = {
  instance?: {
    displayName?: unknown
    subtitle?: unknown
  }
  ui?: {
    chat?: {
      functionType?: unknown
      defaultInteractionMode?: unknown
      projectSlot?: unknown
      uiLabels?: unknown
      starterPrompts?: unknown[]
      welcomeMessage?: unknown
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

  const rawUiLabels = isObject(chatConfig.uiLabels) ? chatConfig.uiLabels : {}
  const normalizedUiLabels = toCanvasUiLabels(rawUiLabels)
  const productName = toText(rawUiLabels.product_name)
    || toText(payload?.instance?.displayName)
    || DEFAULT_CANVAS_UI_LABELS.product_name
  const brandTag = toText(rawUiLabels.brand_tag)
    || toText(payload?.instance?.subtitle)
    || DEFAULT_CANVAS_UI_LABELS.brand_tag
  const starterPrompts = toStarterPrompts(chatConfig.starterPrompts)
  return {
    functionType: DEFAULT_FUNCTION_TYPE,
    interactionMode: DEFAULT_INTERACTION_MODE,
    projectSlot: DEFAULT_PROJECT_SLOT,
    uiLabels: {
      ...normalizedUiLabels,
      product_name: productName,
      brand_tag: brandTag,
      empty_state_title: toText(rawUiLabels.empty_state_title) || `欢迎来到${productName}`,
      empty_state_description: toText(rawUiLabels.empty_state_description)
        || toText(chatConfig.welcomeMessage)
        || DEFAULT_CANVAS_UI_LABELS.empty_state_description,
    },
    starterPrompts,
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
