/// <reference types="vite/client" />

declare const __XIAOCAI_FLARE_WEB_VERSIONS__: Record<string, string>
declare const __XIAOCAI_BRAND_TOKENS__: Partial<{
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
}>

declare module 'flare-chat-core' {
  import type { ComponentType } from 'react'

  export const App: ComponentType<Record<string, unknown>>
}
