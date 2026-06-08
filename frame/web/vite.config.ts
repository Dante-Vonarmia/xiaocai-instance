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

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    __XIAOCAI_FLARE_WEB_VERSIONS__: JSON.stringify(readFlareWebVersions()),
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
