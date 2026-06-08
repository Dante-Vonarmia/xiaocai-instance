export type XiaocaiBrandTokens = {
  primary: string
  primaryHover: string
  primaryStrong: string
  primaryDark: string
  primarySoft: string
  primarySoftHover: string
  primaryBorder: string
  primaryBorderStrong: string
  primaryBorderSoft: string
  primarySubtleText: string
  sidebarBg: string
  textMuted: string
  iconNeutral: string
  iconMuted: string
  primaryRgb: string
  primaryShadowRgb: string
}

const FALLBACK_BRAND_TOKENS: XiaocaiBrandTokens = {
  primary: '#8b5cf6',
  primaryHover: '#7c3aed',
  primaryStrong: '#6d28d9',
  primaryDark: '#4c1d95',
  primarySoft: '#f5f3ff',
  primarySoftHover: '#ede9fe',
  primaryBorder: '#d8b4fe',
  primaryBorderStrong: '#c084fc',
  primaryBorderSoft: '#ddd6fe',
  primarySubtleText: '#f3e8ff',
  sidebarBg: '#faf5ff',
  textMuted: '#7c6f9f',
  iconNeutral: '#6b5f85',
  iconMuted: '#8b80a8',
  primaryRgb: '139, 92, 246',
  primaryShadowRgb: '76, 29, 149',
}

function configuredBrandTokens(): Partial<XiaocaiBrandTokens> {
  try {
    return __XIAOCAI_BRAND_TOKENS__ || {}
  } catch {
    return {}
  }
}

export const XIAOCAI_BRAND_TOKENS: XiaocaiBrandTokens = {
  ...FALLBACK_BRAND_TOKENS,
  ...configuredBrandTokens(),
}
