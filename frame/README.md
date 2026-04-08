# frame

前端壳层（xiaocai 应用外壳）

## 目录结构

```
frame/
└── web/                # Web 应用
    ├── package.json    # 依赖 FLARE packages
    ├── src/
    │   ├── App.tsx
    │   └── main.tsx
    ├── public/
    └── index.html
```

## 依赖关系

依赖 FLARE packages:
- `@flare/chat-core` - Chat 核心逻辑
- `@flare/chat-ui` - Chat UI 组件
- `@flare/generative-ui` - 生成式 UI

通过相对路径引用:
```json
{
  "dependencies": {
    "@flare/chat-core": "file:../../../F.L.A.R.E/packages/flare-chat-core"
  }
}
```

## 状态

**当前状态**: 占位阶段 - 待从 FLARE xiaocai-instance 复制

**来源**: `/Users/dantevonalcatraz/Development/F.L.A.R.E/apps/xiaocai-instance/frame/web/`

## 开发任务

参见: `docs/project/EXECUTION-PLAN.md` - Task 2
