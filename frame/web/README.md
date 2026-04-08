# xiaocai Frame Web

xiaocai 前端壳 - 基于 React + TypeScript + FLARE packages

## 架构说明

这是一个 **前端壳（Frame）**，职责是：

1. **集成 FLARE chat UI**: 不重新实现 chat，直接使用 FLARE 的 `flare-chat-ui` 组件
2. **配置 xiaocai 特定内容**: 品牌、domain-pack、UI 卡片等
3. **管理认证**: 处理宿主应用 token 换取和状态管理

**重要**:
- Chat UI 在 FLARE 实现，不在这里重复实现
- 这个项目只是一个壳，配置和集成 FLARE 组件
- 业务模板、业务文案、品牌配置属于 instance 层装配

## 分层边界（强制）

- `FLARE` 负责通用能力：交互框架、组件、状态机、协议与插槽。
- `xiaocai instance` 负责业务装配：`starterPrompts`、`uiLabels`、`modeQuickEntries`、品牌文案、上下文绑定。
- 需求若只是“模板/文案/配置”变化，只改 instance，不改 FLARE。

正式约束文档：
- [FLARE 与 Instance 边界约束](/Users/dantevonalcatraz/Development/procurement-agents/docs/architecture/07-flare-instance-boundary.md)

## 目录结构

```
frame/web/
├── src/
│   ├── main.tsx              # React 入口
│   ├── App.tsx               # 应用根组件
│   ├── index.css             # 全局样式
│   │
│   ├── pages/                # 页面组件
│   │   └── ChatPage.tsx      # 对话页面
│   │
│   ├── services/             # 服务层
│   │   └── api.ts            # API 客户端
│   │
│   └── hooks/                # React Hooks
│       └── useChat.ts        # Chat Hook
│
├── package.json              # 依赖配置
├── tsconfig.json             # TypeScript 配置
├── vite.config.ts            # Vite 配置
├── index.html                # HTML 入口
├── .env.example              # 环境变量示例
└── README.md                 # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
cd frame/web
npm install
```

**重要**: 确保已经安装了 FLARE packages：

```bash
# 进入 FLARE 项目安装 packages
cd /Users/dantevonalcatraz/Development/F.L.A.R.E
npm install

# 回到 xiaocai 项目
cd /Users/dantevonalcatraz/Development/procurement-agents/frame/web
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 构建生产版本

```bash
npm run build
```

## 技术栈

- **React 18**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **React Router**: 路由管理
- **React Query**: 数据获取和状态管理
- **Axios**: HTTP 客户端
- **FLARE packages**: Chat UI 和核心功能

## 依赖关系

```
xiaocai-frame-web
    ↓
FLARE packages (flare-chat-ui, flare-chat-core)
    ↓
xiaocai-instance-api (HTTP API)
    ↓
FLARE kernel
```

## 核心功能

### 1. 认证流程

```typescript
// 1. Mock 认证（开发环境）
const { data } = await authApi.exchangeTokenMock('test-user')
localStorage.setItem('access_token', data.access_token)

// 2. 宿主应用认证（生产环境）
const { data } = await authApi.exchangeTokenHost(hostToken)
localStorage.setItem('access_token', data.access_token)
```

### 2. 对话功能

```typescript
// 使用 useChat hook
const { messages, sendMessage, isLoading } = useChat()

// 发送消息
await sendMessage('我需要采购一批办公电脑')
```

### 3. FLARE 组件集成

```tsx
import { ChatWorkspace } from '@flare/chat-ui'

<ChatWorkspace
  functionType="requirement_canvas"
  sessionAPI={sessionAPI}
  messageAPI={messageAPI}
  streamAPI={streamAPI}
/>
```

## 开发注意事项

1. **不要重新实现 chat UI** - 使用 FLARE 的 ChatWorkspace
2. **domain-pack 配置** - UI 卡片、术语等从 domain-pack/ 读取
3. **Token 管理** - 使用 localStorage 存储，注意安全性
4. **SSE 流式响应** - 使用 `fetch` 读取 `text/event-stream`

## 参考文档

- 业务需求: `../../docs/discussions/phase-1-*.md`
- UI 卡片配置: `../../domain-pack/cards/procurement-ui-cards.yaml`
- FLARE 文档: `/Users/dantevonalcatraz/Development/F.L.A.R.E/`
