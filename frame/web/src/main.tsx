/**
 * React 应用入口
 *
 * 职责:
 * 1. 挂载 React 根组件
 * 2. 配置 React Query
 * 3. 配置路由
 */

import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { setupIosViewportHeightSync } from './hooks/use-ios-viewport-height'
import 'flare-chat-ui/style.css'
import './index.css'
import './styles/ios-safari.css'
import './theme/xiaocaiFlareTheme.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

setupIosViewportHeightSync()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
)
