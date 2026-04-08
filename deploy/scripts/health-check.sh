#!/bin/bash

# xiaocai 健康检查脚本
# 用途: 检查 instance 服务（可选检查 devlib flare）

set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

API_PORT=${API_PORT:-8001}
WEB_PORT=${WEB_PORT:-3001}
KERNEL_PORT=${KERNEL_PORT:-8000}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_PORT=${REDIS_PORT:-6379}
QDRANT_HTTP_PORT=${QDRANT_HTTP_PORT:-6333}
ENABLE_DEVLIB_FLARE=${ENABLE_DEVLIB_FLARE:-false}

echo "========================================="
echo "   xiaocai instance 服务健康检查"
echo "========================================="
echo ""

# 检查函数
check_service() {
    local name=$1
    local url=$2
    local retries=5
    local count=0

    echo -n "检查 ${name}... "

    while [ $count -lt $retries ]; do
        if curl -sf "${url}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 正常${NC}"
            return 0
        fi
        count=$((count + 1))
        sleep 2
    done

    echo -e "${RED}✗ 失败${NC}"
    return 1
}

check_tcp_port() {
    local name=$1
    local port=$2
    local retries=5
    local count=0

    echo -n "检查 ${name} 端口(${port})... "

    while [ $count -lt $retries ]; do
        if nc -z localhost "${port}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 正常${NC}"
            return 0
        fi
        count=$((count + 1))
        sleep 2
    done

    echo -e "${RED}✗ 失败${NC}"
    return 1
}

# 检查各个服务
all_ok=true

# 1. 检查 API
if ! check_service "inst-xiaocai-api" "http://localhost:${API_PORT}/health"; then
    all_ok=false
fi

# 2. 检查 Web
if ! check_service "inst-xiaocai-web" "http://localhost:${WEB_PORT}"; then
    all_ok=false
fi

# 3. 检查 Infra 端口
if ! check_tcp_port "inst-xiaocai-postgres" "${POSTGRES_PORT}"; then
    all_ok=false
fi
if ! check_tcp_port "inst-xiaocai-redis" "${REDIS_PORT}"; then
    all_ok=false
fi
if ! check_service "inst-xiaocai-qdrant" "http://localhost:${QDRANT_HTTP_PORT}/"; then
    all_ok=false
fi

if [ "$ENABLE_DEVLIB_FLARE" = true ]; then
    # 4. 检查 devlib kernel
    if ! check_service "devlib-flare-kernel" "http://localhost:${KERNEL_PORT}/health"; then
        all_ok=false
    fi
else
    echo -e "${YELLOW}跳过 devlib flare 健康检查（ENABLE_DEVLIB_FLARE=false）${NC}"
fi

echo ""
echo "========================================="

if [ "$all_ok" = true ]; then
    echo -e "${GREEN}所有服务运行正常！${NC}"
    exit 0
else
    echo -e "${RED}部分服务运行异常${NC}"
    echo ""
    echo "查看详细日志:"
    echo "  make logs-instance"
    echo "  make logs-devlib"
    exit 1
fi
