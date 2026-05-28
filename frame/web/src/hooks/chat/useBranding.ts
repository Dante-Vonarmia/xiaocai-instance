import { useEffect, useState } from 'react'

import {
  DEFAULT_CANVAS_UI_LABELS,
  DEFAULT_FUNCTION_TYPE,
  DEFAULT_INTERACTION_MODE,
  DEFAULT_INSTANCE_PROFILE,
  DEFAULT_PROJECT_SLOT,
  DEFAULT_STARTER_PROMPTS,
  type CanvasUiLabels,
  type InstanceProfile,
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
  instanceProfile: InstanceProfile
  starterPrompts: StarterPrompt[]
}

type BrandingPayload = {
  instance?: {
    displayName?: unknown
    subtitle?: unknown
  }
  branding?: {
    logo?: {
      light?: unknown
      dark?: unknown
      sidebar?: unknown
      favicon?: unknown
      wordmark?: unknown
    }
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
  instanceProfile: DEFAULT_INSTANCE_PROFILE,
  starterPrompts: DEFAULT_STARTER_PROMPTS,
}

function toInstanceProfile(
  payload: BrandingPayload | null | undefined,
  uiLabels: CanvasUiLabels,
): InstanceProfile {
  const logoUrl = toText(payload?.branding?.logo?.light) || DEFAULT_INSTANCE_PROFILE.logo_url
  const sidebarLogoUrl = toText(payload?.branding?.logo?.sidebar)
    || toText(payload?.branding?.logo?.wordmark)
    || logoUrl
  const logoText = uiLabels.product_name
  const logoAlt = logoText

  return {
    product_name: uiLabels.product_name,
    brand_tag: uiLabels.brand_tag,
    logo_text: logoText,
    logo_url: logoUrl,
    ui_labels: {
      ...uiLabels,
      empty_state_logo_alt: logoAlt,
      empty_state_logo_url: logoUrl,
      logo_alt: logoAlt,
      logo_url: logoUrl,
      product_logo_alt: logoAlt,
      product_logo_url: logoUrl,
      sidebar_logo_alt: logoAlt,
      sidebar_logo_url: sidebarLogoUrl,
    },
  }
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
  const uiLabels = {
    ...normalizedUiLabels,
    product_name: productName,
    brand_tag: brandTag,
    empty_state_title: toText(rawUiLabels.empty_state_title) || `欢迎来到${productName}`,
    empty_state_description: toText(rawUiLabels.empty_state_description)
      || toText(chatConfig.welcomeMessage)
      || DEFAULT_CANVAS_UI_LABELS.empty_state_description,
  }

  return {
    functionType: DEFAULT_FUNCTION_TYPE,
    interactionMode: DEFAULT_INTERACTION_MODE,
    projectSlot: DEFAULT_PROJECT_SLOT,
    uiLabels,
    instanceProfile: toInstanceProfile(payload, uiLabels),
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
