#!/bin/bash

echo "================================================"
echo "   AI Financial Advisor - Docker 启动"
echo "================================================"
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "[错误] Docker未运行，请先启动Docker"
    exit 1
fi

echo "[1/3] 停止并删除旧容器..."
docker-compose down

echo ""
echo "[2/3] 构建Docker镜像..."
docker-compose build

echo ""
echo "[3/3] 启动服务..."
docker-compose up -d

echo ""
echo "================================================"
echo "   服务启动成功！"
echo "================================================"
echo ""
echo "访问地址:"
echo "  - 主页: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo ""
echo "邀请码: JEFF"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "================================================"

