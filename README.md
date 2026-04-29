# xiaocai-instance 采购助手实例仓库

本仓库是 **xiaocai 的主实例仓库**，不是旧的多仓工作区占位目录。  
它基于 FLARE 提供的通用能力，承接采购场景下的产品编排、领域语义与交付部署。

---

## 1. 当前仓库定位（2026）

- ✅ **这是一个真实 Git 仓库**（不是“local workspace only”）
- ✅ 主要包含：
  - `frame/web`：xiaocai 前端壳（集成 chat-core）
  - `adapters/http_api`：xiaocai instance API（FastAPI）
  - `adapters/kernel`：xiaocai 仓内 kernel 服务壳
  - `domain-packs`：采购领域资产主源（workflow/prompts/knowledge/contracts）
  - `tenant-config`：tenant override（品牌、术语、开关差异）
  - `bindings`：tenant 私有数据绑定描述
  - `deploy`：容器编排、发布脚本、Nginx 配置
- ❌ 不再使用 README 里旧的 `xiaocai-app / xiaocai-api / xiaocai-kernel` 多仓描述

---

## 2. 目录结构（实际）

```text
procurement-agents/
├── adapters/
│   └── http_api/                 # xiaocai instance API adapter, FastAPI
├── frame/
│   └── web/                      # xiaocai 前端壳（Vite + React）
├── deploy/                       # compose / env / nginx / 发布脚本
├── domain-packs/                 # 领域资产主源（采购语义）
├── tenant-config/                # tenant override
├── bindings/                     # tenant 私有数据绑定描述
├── docs/
├── tests/
└── README.md
```

---

## 3. 本地启动（推荐）

### 3.1 前置依赖

- Docker
- Docker Compose v2（`docker compose`）
- Node.js 18+

### 3.2 一键启动 instance 基线（默认包含 kernel）

```bash
cd deploy
make init
make up-instance
```

访问地址：

- Web: [http://localhost:23001](http://localhost:23001)
- API docs: [http://localhost:28001/docs](http://localhost:28001/docs)
- Kernel health: [http://localhost:28000/kernel/health](http://localhost:28000/kernel/health)

### 3.3 常用命令

```bash
cd deploy
make ps-instance
make logs-instance
make db-migrate
make health
make api-smoke
make down-instance
```

---

## 4. 认证与会话（当前行为）

- 本地开发默认可用 mock 登录（取决于 `deploy/.env` 的 `MOCK_AUTH`）
- 会话与项目隔离由 instance API 负责，核心数据范围基于：
  - `user_id`
  - `project_id`

如需强制生产策略，请在部署环境中确认：

- `ENABLE_DEVLIB_FLARE=false`
- `MOCK_AUTH=false`
- `INSTANCE_JWT_SECRET`、`ROOT_AUTH_TOKEN` 非占位值

---

## 5. 发布到服务器（当前推荐正式流程）

当前推荐路径：

- 后端、中间件与 kernel：`compose.instance.yml`
- 前端：**本地构建 standalone dist + 服务器主机 nginx**
- 不依赖远端 `inst-xiaocai-web/inst-xiaocai-nginx` 容器首发

正式发布命令（本地执行）：

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents

FRONTEND_API_BASE_URL=/api \
API_UPSTREAM_URL=http://127.0.0.1:8001 \
REMOTE_HOST=aliyun-xiaocai \
REMOTE_DIR=~/mnt/xiaocai-instance \
FRONTEND_DEPLOY_MODE=standalone \
./deploy/scripts/release-to-aliyun-xiaocai.sh
```

它串联以下步骤：

1. 上传仓库到远端（默认 `/opt/xiaocai-instance`）
2. 远端执行 **backend-only instance** 部署脚本
3. 本地构建 `frame/web` 静态资源
4. 发布前端静态资源到服务器主机
5. 安装/重载服务器主机 Nginx 配置

如果要一起覆盖远端生产环境文件：

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents

COPY_PROD_ENV=true \
FRONTEND_API_BASE_URL=/api \
API_UPSTREAM_URL=http://127.0.0.1:8001 \
REMOTE_HOST=aliyun-xiaocai \
REMOTE_DIR=~/mnt/xiaocai-instance \
FRONTEND_DEPLOY_MODE=standalone \
./deploy/scripts/release-to-aliyun-xiaocai.sh
```

相关脚本：

- `/deploy/scripts/upload-instance-to-aliyun-xiaocai.sh`
- `/deploy/scripts/remote-deploy-instance.sh`
- `/deploy/scripts/deploy-frontend-standalone-to-aliyun-xiaocai.sh`
- `/deploy/scripts/release-to-aliyun-xiaocai.sh`

---

## 6. 服务器清理与重部署建议

若服务器存在历史遗留目录/镜像，可按“清理后重建”执行：

1. 清理旧代码目录（保留当前目标目录）
2. 清理旧容器与旧镜像
3. 上传当前仓库最新代码
4. 重新 build + up + migrate + health

> 注意：清理命令可能删除同机其他项目镜像，请先确认服务器用途。

---

## 7. 常见问题

### Q1: `API 预检失败: 404`

通常是路径兼容问题（如 `/chat/sessions`、`/projects`）。  
请先确认 API 已使用当前仓库版本重新构建并重启。

### Q2: 为什么现在推荐 frontend standalone，而不是远端 web/nginx 容器

因为这条链路更稳，能绕开：

- 远端 `docker-compose`/`docker compose` 差异
- 远端 web 镜像拉取失败
- 远端 web 构建对仓库目录名的隐式假设
- 首发时 nginx reload 因 pid 文件不存在失败

### Q3: 前端显示用户不对（回落到默认用户）

请确认：

- 当前页面不是旧 standalone core 的 iframe 页面
- token 与 `current_user_id` 已正确写入并透传到 chat-core app

---

## 8. 关联文档

- `/AGENTS.md`
- `/QUICKSTART.md`
- `/deploy/README.md`
- `/docs/operations/flare-package-release-consumption-policy.md`

---

## 9. License

Proprietary - Internal use only
