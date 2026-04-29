# xiaocai Deploy (Instance-first)

本目录采用 **instance 交付优先** 的部署规范。

- 生产/交付：只部署 `instance`。
- `FLARE`：生产作为依赖包消费。
- `kernel`：属于 `instance` baseline，随 instance 一起启动，由 xiaocai 仓内服务壳承载。
- `devlib-flare`：仅开发叠加层。
- 依赖消费策略：必须遵守 [FLARE 依赖发布与消费规范](../docs/operations/flare-package-release-consumption-policy.md)。

---

## 1. 命名规范（强约束）

### 1.1 Compose 项目
- `inst-xiaocai-*`：instance 项目
- `devlib-flare-*`：开发辅助（仅 devlib）
- 本地默认 project：`inst-xiaocai-dev`

### 1.2 服务/容器
- `inst-xiaocai-api`
- `inst-xiaocai-web`
- `inst-xiaocai-nginx`
- `inst-xiaocai-postgres`
- `inst-xiaocai-redis`
- `inst-xiaocai-qdrant`
- `inst-xiaocai-kernel`

命名语义：
- `inst`：交付实例（真正上线对象）
- `xiaocai`：业务实例标识
- `api/web/nginx`：实例运行组件
- `kernel`：实例基线内的真实 kernel 服务
- `devlib`：开发期叠加组件（不属于交付对象）

旧名迁移映射：
- `xiaocai-api` -> `inst-xiaocai-api`
- `xiaocai-web` -> `inst-xiaocai-web`
- `xiaocai-nginx` -> `inst-xiaocai-nginx`
- `flare-kernel` -> `inst-xiaocai-kernel`

### 1.3 Compose 文件
- `compose.instance.yml`：交付基线（只含 instance）
- `compose.devlib-flare.yml`：开发叠加层（只含 devlib flare）

---

## 2. 快速开始

```bash
cd deploy
make init
```

编辑 `.env`，至少确认：
- `INSTANCE_PROJECT`
- `INSTANCE_NETWORK_NAME`
- `ENABLE_DEVLIB_FLARE`
- `KERNEL_HOST`

---

## 3. 启动模式

### 3.1 交付基线（推荐默认，包含 kernel）
```bash
make up-instance
```

说明：
- 推荐始终通过 `make` 启动。
- 若必须手动执行 `docker compose`，也应使用 `INSTANCE_PROJECT` 对应的同一 project name。
- `compose.instance.yml` 已显式固定默认 project name，避免在 `deploy/` 目录直接执行时意外生成 `deploy` 这一套额外栈。

### 3.2 开发联调（instance baseline + devlib overlay）
```bash
make up-dev
```

---

## 4. 常用命令

```bash
make ps-instance
make logs-instance
make down-instance

make ps-dev
make logs-dev
make logs-devlib
make down-dev

make health
make api-smoke
make db-migrate
```

首次初始化或切换数据库后，建议先执行：

```bash
make db-migrate
```

---

## 5. 环境变量说明（关键项）

### 5.1 命名与模式
- `INSTANCE_PROJECT=inst-xiaocai-dev`
- `INSTANCE_NETWORK_NAME=inst-xiaocai-net-dev`
- `ENABLE_DEVLIB_FLARE=true|false`（仅控制 devlib overlay，不影响 baseline kernel）

### 5.2 Kernel 指向
- 优先使用：`KERNEL_BASE_URL=http://<真实-kernel-host>:<port>`
- instance baseline 默认：`KERNEL_HOST=inst-xiaocai-kernel`
- 指向宿主机真实 kernel 时：`KERNEL_HOST=host.docker.internal`
- 推荐实例模式：`KERNEL_RUNTIME_MODE=http`（通过 FLARE kernel 服务接口调用）
- 默认路径：`KERNEL_RUN_PATH=/kernel/run`、`KERNEL_STREAM_PATH=/kernel/stream`

### 5.3 xiaocai instance 参数
- `KERNEL_RUNTIME_MODE`
- `KERNEL_RUN_PATH`
- `KERNEL_STREAM_PATH`
- `STORAGE_DB_URL`
- `STORAGE_DB_PATH`
- `UPLOAD_ROOT`
- `REDIS_URL`
- `QDRANT_URL`
- `FLARE_POSTGRES_DSN`
- `FLARE_REDIS_URL`
- `FLARE_QDRANT_URL`
- `FLARE_SOURCE_UPLOAD_DIR`
- `UPLOAD_MAX_SIZE_BYTES`
- `UPLOAD_ALLOWED_EXTENSIONS`
- `ENABLED_MODES`
- `DAILY_MESSAGE_LIMIT`
- `DAILY_PROJECT_MESSAGE_LIMIT`
- `LLM_PROVIDER_BACKEND`
- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `DASHSCOPE_MODEL`

推荐持久化配置（已在 `.env.example` 给出）：
- `STORAGE_DB_URL=postgresql://...`
- `STORAGE_DB_PATH=/data/xiaocai-instance.db`
- `UPLOAD_ROOT=/data/uploads`
- API 服务挂载命名卷：`inst-xiaocai-api-data:/data`
- `inst-xiaocai-postgres` / `inst-xiaocai-redis` / `inst-xiaocai-qdrant` 由 instance compose 统一编排

---

## 6. 边界声明（避免后续混乱）

1. `instance` 是交付对象。  
2. `FLARE` 在生产是库，不是独立部署服务。  
3. `inst-xiaocai-kernel` 属于 instance baseline。  
4. 不允许同机并行运行另一套 `xiaocai-platform` 且占用同端口。
5. 不允许通过 `file:` 或 `COPY F.L.A.R.E/packages` 方式引入 FLARE 源码进入交付镜像。

---

## 7. 排障

### 7.1 看到多个相似容器名
通常是两套 stack 并行：`instance` 和旧 `platform`。  
先停旧 stack，再只用本目录 `make` 命令启动。

### 7.2 API 可用但回复仍是 mock
当前链路仍在 baseline kernel。  
检查 `KERNEL_HOST` 是否符合预期。

### 7.3 会话/资料读取异常，怀疑库表未初始化
执行：

```bash
make db-migrate
```

再查看 API 日志确认迁移输出：`[xiaocai-db-migrate] backend=... version=2`

---

## 8. 生产发布（当前推荐：backend-only compose + frontend standalone）

适用目标：
- 后端、中间件与 kernel 走 `compose.instance.yml`
- 前端静态资源独立部署到服务器主机 Nginx
- 远端默认不依赖 `inst-xiaocai-web/inst-xiaocai-nginx`
- 首发先 `IP + HTTP` 验证

### 8.1 准备生产环境文件

本地生成：

```bash
cd deploy
cp .env.production.example .env.production
```

按实际值填写 `.env.production`，并确认：
- `ENABLE_DEVLIB_FLARE=false`
- `MOCK_AUTH=false`
- `ROOT_AUTH_TOKEN` 非空
- `INSTANCE_JWT_SECRET` 非空
- `STORAGE_DB_URL` 使用 `postgresql://...`
- `KERNEL_BASE_URL` 或 `KERNEL_HOST/KERNEL_PORT` 指向真实 kernel

### 8.2 上传代码到服务器

```bash
REMOTE_HOST=aliyun-xiaocai \
REMOTE_DIR=~/mnt/xiaocai-instance \
./scripts/upload-instance-to-aliyun-xiaocai.sh
```

如需自动覆盖远端 `deploy/.env`：

```bash
scp .env.production aliyun-xiaocai:/opt/xiaocai-instance/deploy/.env
```

### 8.3 远端部署 instance（短停机切换）

在服务器执行：

```bash
REPO_DIR=~/mnt/xiaocai-instance \
FRONTEND_DEPLOY_MODE=standalone \
bash ~/mnt/xiaocai-instance/deploy/scripts/remote-deploy-instance.sh
```

若 kernel 暂时不可达，可先跳过 smoke：

```bash
REPO_DIR=~/mnt/xiaocai-instance \
SKIP_API_SMOKE=true \
FRONTEND_DEPLOY_MODE=standalone \
bash ~/mnt/xiaocai-instance/deploy/scripts/remote-deploy-instance.sh
```

该脚本包含：
1. `make config-instance`
2. `make backup-db`（若已有运行栈）
3. `make down-instance`
4. standalone 模式下执行 `make up-instance-backend`
5. `make db-migrate`
6. standalone 模式下执行 `CHECK_WEB=false make health`
7. `make api-smoke`

### 8.4 前端独立部署

本地构建（首发 HTTP）：

```bash
cd ../frame/web
API_BASE_URL=http://47.101.138.75:8001 ./scripts/build-standalone.sh
```

上传并安装远端 Nginx 配置：

```bash
cd ../../deploy
REMOTE_HOST=aliyun-xiaocai \
API_UPSTREAM_URL=http://127.0.0.1:8001 \
SERVER_NAME=_ \
./scripts/deploy-frontend-standalone-to-aliyun-xiaocai.sh
```

Nginx 模板：`deploy/nginx/frontend-standalone-http.conf.template`

### 8.5 一键串联发布（正式推荐）

```bash
cd /Users/dantevonalcatraz/Development/procurement-agents

FRONTEND_API_BASE_URL=/api \
API_UPSTREAM_URL=http://127.0.0.1:8001 \
REMOTE_HOST=aliyun-xiaocai \
REMOTE_DIR=~/mnt/xiaocai-instance \
FRONTEND_DEPLOY_MODE=standalone \
COPY_PROD_ENV=true \
./deploy/scripts/release-to-aliyun-xiaocai.sh
```

注意：
- `COPY_PROD_ENV=true` 前需要本地存在 `deploy/.env.production`
- 若你不希望脚本覆盖远端 `.env`，把 `COPY_PROD_ENV` 设为 `false`
- `FRONTEND_DEPLOY_MODE=standalone` 是当前推荐默认值

### 8.6 当前推荐路径为什么更稳

这条链路专门规避了最近已经踩过的几个问题：

- 远端只有 `docker compose`，没有 `docker-compose`
- 远端 repo 目录名变化导致 web Dockerfile 路径失效
- 远端 web 镜像构建依赖 Docker Hub，容易超时
- 首次前端部署时 `nginx -s reload` 可能因为 pid 不存在失败
- standalone 前端上传时 macOS xattr 会产生无意义 tar 警告
