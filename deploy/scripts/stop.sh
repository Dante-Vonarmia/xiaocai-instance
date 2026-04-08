#!/bin/bash

# xiaocai 停止脚本
# 用途: 停止 instance 与 devlib flare 服务

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   停止 instance/devlib 服务${NC}"
echo -e "${GREEN}========================================${NC}"

# 切换到 deploy 目录
cd "$(dirname "$0")/.."

echo -e "${GREEN}停止 devlib 服务（如果存在）...${NC}"
make down-dev || true
echo -e "${GREEN}停止 instance 服务（如果存在）...${NC}"
make down-instance || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   instance/devlib 服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "如需删除数据卷，请手动执行 compose down -v（按对应 compose 文件）"
echo -e "重新启动服务: ${YELLOW}./scripts/start.sh${NC}"
echo ""
