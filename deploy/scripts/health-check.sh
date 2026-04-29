#!/bin/bash

# xiaocai 健康检查脚本
# 用途: 检查 instance baseline 服务（默认包含 kernel）

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

API_PORT=28001
WEB_PORT=23001
KERNEL_PORT=28000
POSTGRES_PORT=25432
REDIS_PORT=26379
QDRANT_HTTP_PORT=26333
CHECK_WEB=${CHECK_WEB:-true}

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
if [ "$CHECK_WEB" = true ]; then
    if ! check_service "inst-xiaocai-web" "http://localhost:${WEB_PORT}"; then
        all_ok=false
    fi
else
    echo -e "${YELLOW}跳过 inst-xiaocai-web 健康检查（CHECK_WEB=false）${NC}"
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

# 4. 检查 baseline kernel
if ! check_service "inst-xiaocai-kernel" "http://localhost:${KERNEL_PORT}/kernel/health"; then
    all_ok=false
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
    exit 1
fi
