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
import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  optimizeDeps: {
    include: ['style-to-js', 'hast-util-to-jsx-runtime'],
  },

  resolve: {
    preserveSymlinks: true,
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
