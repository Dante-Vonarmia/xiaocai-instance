# adapters

适配器层（HTTP API 适配）

## 目录结构

```
adapters/
└── http_api/           # HTTP API 适配器
    ├── auth.py         # POST /auth/exchange - 身份换取
    ├── chat.py         # POST /chat/run, /chat/stream - 对话接口
    ├── main.py         # FastAPI 入口
    └── requirements.txt
```

## 核心接口

| 接口 | 说明 |
|------|------|
| `POST /auth/exchange` | 宿主应用身份换取本系统 access_token |
| `POST /chat/run` | 同步对话接口 |
| `POST /chat/stream` | 流式对话接口（SSE） |

## 依赖关系

依赖 FLARE kernel:
- `flare-kernel` (Python package)
- `flare-kernel-client-py`

## 状态

**当前状态**: 占位阶段 - 待从 FLARE xiaocai-instance 复制

**来源**: `/Users/dantevonalcatraz/Development/F.L.A.R.E/apps/xiaocai-instance/adapters/http_api/`

## 开发任务

参见: `docs/project/EXECUTION-PLAN.md` - Task 3
