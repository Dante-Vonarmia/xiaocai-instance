/**
 * Vite 配置
 *
 * 职责:
 * 1. 配置 React plugin
 * 2. 配置开发服务器
 * 3. 配置路径别名
 * 4. 配置代理（API 转发）
 */

import { fileURLToPath } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const FLARE_WEB_PACKAGES = [
  'flare-chat-core',
  'flare-chat-ui',
  'flare-canvas-ui',
  'flare-generative-ui',
]
const DEFAULT_BRAND_TOKENS = {
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

function readJsonFile(filePath: string) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8')) as Record<string, unknown>
}

function readFlareWebVersions() {
  const packageJson = readJsonFile(path.resolve(__dirname, 'package.json'))
  const packageLock = readJsonFile(path.resolve(__dirname, 'package-lock.json'))
  const rootPackage = packageLock.packages as Record<string, { version?: string }> | undefined
  const dependencies = packageJson.dependencies as Record<string, string> | undefined
  const versions: Record<string, string> = {}

  for (const packageName of FLARE_WEB_PACKAGES) {
    const directVersion = dependencies?.[packageName]
    const lockedVersion = rootPackage?.[`node_modules/${packageName}`]?.version
    versions[packageName] = String(lockedVersion || directVersion || '').replace(/^[~^=]/, '')
  }
  return versions
}

function hexToRgb(value: unknown) {
  const text = String(value || '').trim().replace(/^#/, '')
  if (!/^[0-9a-fA-F]{6}$/.test(text)) {
    return DEFAULT_BRAND_TOKENS.primaryRgb
  }
  const red = parseInt(text.slice(0, 2), 16)
  const green = parseInt(text.slice(2, 4), 16)
  const blue = parseInt(text.slice(4, 6), 16)
  return `${red}, ${green}, ${blue}`
}

function brandingConfigPath() {
  const candidates = [
    path.resolve(__dirname, 'domain-packs/branding/instance-branding.json'),
    path.resolve(__dirname, '../../domain-packs/branding/instance-branding.json'),
  ]
  return candidates.find((candidate) => fs.existsSync(candidate))
}

function readBrandTokens() {
  const configPath = brandingConfigPath()
  if (!configPath) {
    return DEFAULT_BRAND_TOKENS
  }
  const config = readJsonFile(configPath)
  const branding = config.branding as Record<string, unknown> | undefined
  const colors = branding?.colors as Record<string, unknown> | undefined
  const primary = String(colors?.primary || DEFAULT_BRAND_TOKENS.primary)
  return {
    ...DEFAULT_BRAND_TOKENS,
    primary,
    primaryHover: String(colors?.accent || DEFAULT_BRAND_TOKENS.primaryHover),
    primaryStrong: String(colors?.secondary || DEFAULT_BRAND_TOKENS.primaryStrong),
    primaryRgb: hexToRgb(primary),
  }
}

function brandTokenCss(tokens: typeof DEFAULT_BRAND_TOKENS) {
  return `:root{${Object.entries({
    '--xiaocai-brand-primary': tokens.primary,
    '--xiaocai-brand-primary-hover': tokens.primaryHover,
    '--xiaocai-brand-primary-strong': tokens.primaryStrong,
    '--xiaocai-brand-primary-dark': tokens.primaryDark,
    '--xiaocai-brand-primary-soft': tokens.primarySoft,
    '--xiaocai-brand-primary-soft-hover': tokens.primarySoftHover,
    '--xiaocai-brand-primary-border': tokens.primaryBorder,
    '--xiaocai-brand-primary-border-strong': tokens.primaryBorderStrong,
    '--xiaocai-brand-primary-border-soft': tokens.primaryBorderSoft,
    '--xiaocai-brand-primary-subtle-text': tokens.primarySubtleText,
    '--xiaocai-brand-sidebar-bg': tokens.sidebarBg,
    '--xiaocai-brand-text-muted': tokens.textMuted,
    '--xiaocai-brand-icon-neutral': tokens.iconNeutral,
    '--xiaocai-brand-icon-muted': tokens.iconMuted,
    '--xiaocai-brand-primary-rgb': tokens.primaryRgb,
    '--xiaocai-brand-primary-shadow-rgb': tokens.primaryShadowRgb,
    '--xiaocai-primary': 'var(--xiaocai-brand-primary)',
    '--xiaocai-primary-hover': 'var(--xiaocai-brand-primary-hover)',
    '--xiaocai-primary-strong': 'var(--xiaocai-brand-primary-strong)',
    '--xiaocai-primary-dark': 'var(--xiaocai-brand-primary-dark)',
    '--xiaocai-primary-soft': 'var(--xiaocai-brand-primary-soft)',
    '--xiaocai-primary-soft-hover': 'var(--xiaocai-brand-primary-soft-hover)',
    '--xiaocai-primary-border': 'var(--xiaocai-brand-primary-border)',
    '--xiaocai-primary-border-strong': 'var(--xiaocai-brand-primary-border-strong)',
    '--xiaocai-primary-border-soft': 'var(--xiaocai-brand-primary-border-soft)',
    '--xiaocai-primary-rgb': 'var(--xiaocai-brand-primary-rgb)',
    '--xiaocai-primary-shadow-rgb': 'var(--xiaocai-brand-primary-shadow-rgb)',
    '--xiaocai-focus-ring': '0 0 0 3px rgba(var(--xiaocai-primary-rgb), 0.18)',
  }).map(([key, value]) => `${key}:${value}`).join(';')}}`
}

const brandTokens = readBrandTokens()

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    {
      name: 'xiaocai-brand-token-preload',
      transformIndexHtml() {
        return [
          {
            tag: 'style',
            attrs: { id: 'xiaocai-brand-tokens' },
            children: brandTokenCss(brandTokens),
            injectTo: 'head-prepend',
          },
        ]
      },
    },
    react(),
  ],
  define: {
    __XIAOCAI_FLARE_WEB_VERSIONS__: JSON.stringify(readFlareWebVersions()),
    __XIAOCAI_BRAND_TOKENS__: JSON.stringify(brandTokens),
  },

  optimizeDeps: {
    include: ['style-to-js', 'hast-util-to-jsx-runtime', 'debug'],
    needsInterop: ['debug'],
  },

  resolve: {
    preserveSymlinks: false,
    dedupe: ['react', 'react-dom', 'antd', '@ant-design/icons'],
    alias: {
      '@': path.resolve(__dirname, './src'),
      './renderers/renderModeArtifactBlock.jsx': path.resolve(
        __dirname,
        './src/shims/renderModeArtifactBlock.jsx'
      ),
      '../renderers/renderModeArtifactBlock.jsx': path.resolve(
        __dirname,
        './src/shims/renderModeArtifactBlock.jsx'
      ),
      '@rc-component/context': path.resolve(
        __dirname,
        './node_modules/@rc-component/context/es/index.js'
      ),
    },
  },

  server: {
    port: 9001,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
  },

  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
})
