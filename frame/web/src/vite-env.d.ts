/// <reference types="vite/client" />

declare const __XIAOCAI_FLARE_WEB_VERSIONS__: Record<string, string>

declare module 'flare-chat-core' {
  import type { ComponentType } from 'react'

  export const App: ComponentType<Record<string, unknown>>
}
