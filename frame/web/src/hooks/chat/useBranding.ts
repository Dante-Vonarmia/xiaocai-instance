import { useEffect, useState } from 'react'

import {
  DEFAULT_APP_BRANDING,
  DEFAULT_CAPABILITY_CATALOG,
  DEFAULT_CANVAS_UI_LABELS,
  DEFAULT_COMPOSER_MODE_OPTIONS,
  DEFAULT_DISPLAY_POLICY,
  DEFAULT_FUNCTION_TYPE,
  DEFAULT_INTERACTION_MODE,
  DEFAULT_INSTANCE_PROFILE,
  DEFAULT_MODULE_PROMPT_REGISTRY,
  DEFAULT_PROJECT_SLOT,
  DEFAULT_STARTER_PROMPTS,
  type AppBranding,
  type CapabilityCatalogItem,
  type CanvasUiLabels,
  type ComposerModeOption,
  type DisplayPolicy,
  type InstanceProfile,
  type InteractionMode,
  type ModulePromptRegistryItem,
  type ProjectSlot,
  type StarterPrompt,
} from '@/constants/chat'
import {
  isObject,
  toAppBranding,
  toCapabilityCatalog,
  toCanvasUiLabels,
  toComposerModeOptions,
  toModulePromptRegistry,
  toStarterPrompts,
  toStringRecord,
  toText,
} from '@/hooks/chat/normalizers'

type BrandingState = {
  functionType: string
  interactionMode: InteractionMode
  projectSlot: ProjectSlot
  uiLabels: CanvasUiLabels
  instanceProfile: InstanceProfile
  starterPrompts: StarterPrompt[]
  branding: AppBranding
  displayPolicy: DisplayPolicy
  composerModeOptions: ComposerModeOption[]
  capabilityCatalog: CapabilityCatalogItem[]
  modulePromptRegistry: ModulePromptRegistryItem[]
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

type AppProfilePayload = {
  branding?: unknown
  capabilityCatalog?: unknown
  composerModeOptions?: unknown
  displayPolicy?: unknown
  modulePromptRegistry?: unknown
  instanceProfile?: {
    brand_tag?: unknown
    logo_text?: unknown
    logo_url?: unknown
    product_name?: unknown
    ui_labels?: unknown
  }
  starterScenarios?: unknown
}

const DEFAULT_BRANDING_STATE: BrandingState = {
  functionType: DEFAULT_FUNCTION_TYPE,
  interactionMode: DEFAULT_INTERACTION_MODE,
  projectSlot: DEFAULT_PROJECT_SLOT,
  uiLabels: DEFAULT_CANVAS_UI_LABELS,
  instanceProfile: DEFAULT_INSTANCE_PROFILE,
  starterPrompts: DEFAULT_STARTER_PROMPTS,
  branding: DEFAULT_APP_BRANDING,
  displayPolicy: DEFAULT_DISPLAY_POLICY,
  composerModeOptions: DEFAULT_COMPOSER_MODE_OPTIONS,
  capabilityCatalog: DEFAULT_CAPABILITY_CATALOG,
  modulePromptRegistry: DEFAULT_MODULE_PROMPT_REGISTRY,
}

const APP_PROFILE_PATH = '/domain-packs/xiaocai/app-profile.json'
const LEGACY_BRANDING_PATH = '/domain-packs/branding/instance-branding.json'

function toDisplayPolicy(value: unknown): DisplayPolicy {
  if (!isObject(value)) {
    return DEFAULT_DISPLAY_POLICY
  }
  return {
    showAllStarterScenarios: typeof value.showAllStarterScenarios === 'boolean'
      ? value.showAllStarterScenarios
      : undefined,
    showStarterScenarios: typeof value.showStarterScenarios === 'boolean' ? value.showStarterScenarios : undefined,
    showUserFooter: typeof value.showUserFooter === 'boolean' ? value.showUserFooter : undefined,
  }
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

function toAppProfileInstanceProfile(
  payload: AppProfilePayload,
  uiLabels: CanvasUiLabels & Record<string, string>,
): InstanceProfile {
  const profile = payload.instanceProfile || {}
  const logoUrl = toText(profile.logo_url) || DEFAULT_INSTANCE_PROFILE.logo_url
  const logoText = toText(profile.logo_text) || uiLabels.product_name
  return {
    product_name: uiLabels.product_name,
    brand_tag: uiLabels.brand_tag,
    logo_text: logoText,
    logo_url: logoUrl,
    ui_labels: {
      ...uiLabels,
      logo_alt: uiLabels.logo_alt || logoText,
      logo_url: uiLabels.logo_url || logoUrl,
    },
  }
}

function normalizeUiLabels(
  rawLabels: unknown,
  productName: string,
  brandTag: string,
  fallbackDescription: string,
): CanvasUiLabels & Record<string, string> {
  const normalized = toCanvasUiLabels(rawLabels)
  const stringLabels = toStringRecord(rawLabels)
  return {
    ...normalized,
    ...stringLabels,
    product_name: productName,
    brand_tag: brandTag,
    empty_state_title: toText(stringLabels.empty_state_title) || `欢迎来到${productName}`,
    empty_state_description: toText(stringLabels.empty_state_description) || fallbackDescription,
  }
}

function normalizeAppProfileState(payload: AppProfilePayload | null | undefined): BrandingState | null {
  if (!isObject(payload) || !isObject(payload.instanceProfile)) {
    return null
  }
  const productName = toText(payload.instanceProfile.product_name) || DEFAULT_CANVAS_UI_LABELS.product_name
  const brandTag = toText(payload.instanceProfile.brand_tag) || DEFAULT_CANVAS_UI_LABELS.brand_tag
  const uiLabels = normalizeUiLabels(
    payload.instanceProfile.ui_labels,
    productName,
    brandTag,
    DEFAULT_CANVAS_UI_LABELS.empty_state_description,
  )
  return {
    functionType: DEFAULT_FUNCTION_TYPE,
    interactionMode: DEFAULT_INTERACTION_MODE,
    projectSlot: DEFAULT_PROJECT_SLOT,
    uiLabels,
    instanceProfile: toAppProfileInstanceProfile(payload, uiLabels),
    starterPrompts: toStarterPrompts(payload.starterScenarios),
    branding: toAppBranding(payload.branding),
    displayPolicy: toDisplayPolicy(payload.displayPolicy),
    composerModeOptions: toComposerModeOptions(payload.composerModeOptions),
    capabilityCatalog: toCapabilityCatalog(payload.capabilityCatalog),
    modulePromptRegistry: toModulePromptRegistry(payload.modulePromptRegistry),
  }
}

function normalizeBrandingState(payload: BrandingPayload | null | undefined): BrandingState {
  const chatConfig = payload?.ui?.chat
  if (!chatConfig) {
    return DEFAULT_BRANDING_STATE
  }

  const rawUiLabels = isObject(chatConfig.uiLabels) ? chatConfig.uiLabels : {}
  const productName = toText(rawUiLabels.product_name)
    || toText(payload?.instance?.displayName)
    || DEFAULT_CANVAS_UI_LABELS.product_name
  const brandTag = toText(rawUiLabels.brand_tag)
    || toText(payload?.instance?.subtitle)
    || DEFAULT_CANVAS_UI_LABELS.brand_tag
  const starterPrompts = toStarterPrompts(chatConfig.starterPrompts)
  const uiLabels = normalizeUiLabels(
    rawUiLabels,
    productName,
    brandTag,
    toText(chatConfig.welcomeMessage) || DEFAULT_CANVAS_UI_LABELS.empty_state_description,
  )

  return {
    functionType: DEFAULT_FUNCTION_TYPE,
    interactionMode: DEFAULT_INTERACTION_MODE,
    projectSlot: DEFAULT_PROJECT_SLOT,
    uiLabels,
    instanceProfile: toInstanceProfile(payload, uiLabels),
    starterPrompts,
    branding: toAppBranding(payload.branding),
    displayPolicy: DEFAULT_DISPLAY_POLICY,
    composerModeOptions: DEFAULT_COMPOSER_MODE_OPTIONS,
    capabilityCatalog: DEFAULT_CAPABILITY_CATALOG,
    modulePromptRegistry: DEFAULT_MODULE_PROMPT_REGISTRY,
  }
}

async function loadJson(path: string) {
  const response = await fetch(path, { cache: 'no-store' })
  if (!response.ok) {
    return null
  }
  return response.json()
}

export function useBranding() {
  const [branding, setBranding] = useState<BrandingState>(DEFAULT_BRANDING_STATE)

  useEffect(() => {
    let cancelled = false

    const loadBranding = async () => {
      try {
        const appProfile = normalizeAppProfileState(await loadJson(APP_PROFILE_PATH) as AppProfilePayload | null)
        if (appProfile && !cancelled) {
          setBranding(appProfile)
          return
        }
        const payload = await loadJson(LEGACY_BRANDING_PATH) as BrandingPayload | null
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
