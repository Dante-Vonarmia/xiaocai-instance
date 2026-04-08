#!/bin/bash

# xiaocai 启动脚本
# 用途: 启动实例服务（可选叠加 devlib flare）

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   启动 instance 服务${NC}"
echo -e "${GREEN}========================================${NC}"

# 切换到 deploy 目录
cd "$(dirname "$0")/.."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env 文件不存在，使用 .env.example 创建...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}请编辑 .env 文件填写实际配置后再次运行${NC}"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 检查旧平台容器冲突（会占用 5432/6379/6333/6334）
legacy_conflicts=$(docker ps --format '{{.Names}}' | grep -E '^xiaocai-(postgres|redis|qdrant|api|kernel)$' || true)
if [ -n "$legacy_conflicts" ]; then
    echo -e "${RED}错误: 检测到旧平台容器仍在运行，可能导致 instance 服务端口冲突:${NC}"
    echo "$legacy_conflicts" | sed 's/^/  - /'
    echo -e "${YELLOW}请先停止旧栈（legacy/xiaocai-platform），再启动当前 instance 栈。${NC}"
    exit 1
fi

# 构建镜像（instance）
echo -e "${GREEN}1. 构建 instance 镜像...${NC}"
make build-instance

# 启动服务（instance）
echo -e "${GREEN}2. 启动 instance 服务...${NC}"
make up-instance

# 可选启动 devlib flare
if [ "${ENABLE_DEVLIB_FLARE:-false}" = "true" ]; then
    echo -e "${GREEN}3. 启动 devlib flare 服务...${NC}"
    make up-dev
else
    echo -e "${YELLOW}3. 跳过 devlib flare（ENABLE_DEVLIB_FLARE=false）${NC}"
fi

# 等待服务启动
echo -e "${GREEN}4. 等待服务启动...${NC}"
sleep 5

# 健康检查
echo -e "${GREEN}5. 检查服务状态...${NC}"
./scripts/health-check.sh

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   instance 服务启动成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "前端访问地址: ${GREEN}http://localhost:${WEB_PORT:-3001}${NC}"
echo -e "API 文档地址: ${GREEN}http://localhost:${API_PORT:-8001}/docs${NC}"
echo ""
echo -e "查看 instance 日志: ${YELLOW}make logs-instance${NC}"
echo -e "查看 devlib 日志: ${YELLOW}make logs-devlib${NC}"
echo -e "停止服务: ${YELLOW}./scripts/stop.sh${NC}"
echo ""
