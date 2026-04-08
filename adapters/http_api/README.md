# xiaocai Instance API

xiaocai 采购助手的 HTTP API 适配器，基于 FLARE kernel 提供对话和认证服务。

## 架构说明

这是一个 **FastAPI 适配器**，职责是：

1. **认证管理**: 宿主应用 token / 微信小程序 code 换取 xiaocai JWT token
2. **对话代理**: 接收前端请求，转发给 FLARE kernel，返回响应
3. **权限控制**: 管理用户与 Project/Knowledge 的归属关系

**重要**:
- Chat 核心功能在 FLARE kernel 实现，不在这里重复实现
- 这个服务只是一个薄的适配层

## 目录结构

```
adapters/http_api/
├── src/xiaocai_instance_api/
│   ├── main.py                    # 服务入口
│   ├── app.py                     # FastAPI 工厂
│   ├── settings.py                # 配置管理
│   │
│   ├── contracts/                 # API 契约（请求/响应模型）
│   │   ├── auth_contract.py       # 认证接口
│   │   └── chat_contract.py       # 对话接口
│   │
│   ├── auth/                      # 认证模块
│   │   ├── service.py             # 认证服务
│   │   ├── router.py              # 认证路由
│   │   └── providers/             # 认证提供者
│   │       ├── base.py            # 基类
│   │       ├── mock_provider.py   # Mock 认证
│   │       └── real_provider.py   # 真实认证
│   │
│   ├── chat/                      # 对话模块
│   │   ├── kernel_client.py       # Kernel 客户端
│   │   └── router.py              # 对话路由
│   │
│   ├── security/                  # 安全模块
│   │   ├── token_codec.py         # JWT 编解码
│   │   └── dependencies.py        # FastAPI 依赖注入
│   │
│   └── storage/                   # 存储模块
│       └── ownership_store.py     # 归属关系存储
│
├── tests/                         # 测试
│   ├── test_auth.py
│   └── test_chat.py
│
├── pyproject.toml                 # 包配置
├── .env.example                   # 环境变量示例
└── README.md                      # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
cd adapters/http_api
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写实际配置
```

关键配置项：
- `INSTANCE_JWT_SECRET`: JWT 签名密钥（生产环境务必修改）
- `KERNEL_RUNTIME_MODE`: Kernel 调用模式（仅支持 `http`）
- `KERNEL_HOST` / `KERNEL_PORT`: FLARE kernel 服务地址
- `STORAGE_DB_URL`: 实例数据库连接串（推荐 `postgresql://...`，优先于 `STORAGE_DB_PATH`）
- `STORAGE_DB_PATH`: SQLite 回退路径（仅 `STORAGE_DB_URL` 为空时生效）
- `UPLOAD_ROOT`: 资料文件存储目录
- `REDIS_URL` / `QDRANT_URL`: 实例侧缓存与向量服务地址
- `DASHSCOPE_API_KEY`: 百炼 API Key（由 FLARE kernel 实际消费）
- `MOCK_AUTH`: 开发环境设置为 `true`

### 3. 启动服务

```bash
python -m xiaocai_instance_api.main
```

服务启动在 `http://0.0.0.0:8001`

### 3.1 执行数据库迁移（推荐先执行）

```bash
python -m xiaocai_instance_api.storage.migrate
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API 接口

### 认证接口

#### POST /auth/exchange

身份换取 - 宿主应用 token 或微信 code 换取 xiaocai token

**请求示例（Mock 模式）**:
```json
{
  "mock": true,
  "mock_user_id": "test-user-123"
}
```

**请求示例（宿主应用）**:
```json
{
  "mock": false,
  "host_token": "host-app-token-xxx"
}
```

**请求示例（Root 模式，非 Mock）**:
```json
{
  "mock": false,
  "root_token": "root-local-dev-token"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user_id": "test-user-123"
}
```

### 对话接口

#### POST /chat/run

同步对话 - 等待完整响应

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "message": "我需要采购一批办公电脑",
  "session_id": "session-123",
  "context": {
    "project_id": "proj-456"
  }
}
```

**响应**:
```json
{
  "message": "我理解您需要采购办公电脑，请告诉我具体需求...",
  "cards": [
    {
      "type": "requirement-form",
      "data": {"fields": ["category", "quantity", "budget"]}
    }
  ],
  "session_id": "session-123"
}
```

#### POST /chat/stream

流式对话 - Server-Sent Events (SSE)

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "message": "继续",
  "session_id": "session-123"
}
```

**响应（SSE 流）**:
```
data: {"type": "token", "content": "根据"}
data: {"type": "token", "content": "您的"}
data: {"type": "token", "content": "需求"}
data: {"type": "card", "card": {...}}
data: {"type": "done"}
```

## 业务流程

### 认证流程

1. 前端从宿主应用获取 token 或微信 code
2. 调用 `/auth/exchange` 换取 xiaocai token
3. 使用 xiaocai token 访问其他接口

### 对话流程

1. 前端调用 `/chat/run` 或 `/chat/stream`
2. API 验证 JWT token，提取 user_id
3. API 转发请求给 FLARE kernel
4. Kernel 调用 7 Engine 处理对话
5. API 返回响应给前端

## 测试

```bash
# 运行测试
pytest tests/

# 运行特定测试
pytest tests/test_auth.py -v

# 生成覆盖率报告
pytest --cov=xiaocai_instance_api tests/
```

## 依赖关系

```
xiaocai-instance-api
    ↓
FLARE kernel (独立服务)
    ↓
FLARE 7 Engine
```

## 开发注意事项

1. **不要在这里实现 chat 逻辑** - chat 在 FLARE kernel 实现
2. **保持薄适配层** - 只做请求转发和认证
3. **环境变量管理** - 不要提交 .env 文件到 git
4. **JWT 密钥安全** - 生产环境使用强密钥

## 参考文档

- 业务需求: `docs/discussions/phase-1-*.md`
- 架构设计: `docs/architecture/`
- FLARE 文档: `/Users/dantevonalcatraz/Development/F.L.A.R.E/`
