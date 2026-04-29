/// <reference types="vite/client" />

declare module 'flare-chat-ui' {
  import type { ComponentType } from 'react'

  export const App: ComponentType<Record<string, unknown>>
}
