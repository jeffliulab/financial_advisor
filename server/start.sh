#!/bin/bash
# AI Financial Advisor - Linux/Mac启动脚本
# 
# 使用方法：
#   chmod +x start.sh
#   ./start.sh

echo ""
echo "================================================"
echo "   AI Financial Advisor - 后端服务启动"
echo "================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "[1/4] 检测Python版本..."
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "[2/4] 创建虚拟环境..."
    python3 -m venv venv
    echo "    虚拟环境创建成功！"
else
    echo ""
    echo "[2/4] 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo ""
echo "[3/4] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "[4/4] 检查并安装依赖包..."
pip install -r requirements.txt --quiet

# 检查.env文件
if [ ! -f ".env" ]; then
    echo ""
    echo "================================================"
    echo "[警告] 未找到 .env 配置文件！"
    echo "================================================"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 复制 env.example 的内容"
    echo "2. 创建 .env 文件"
    echo "3. 填写你的API密钥等配置"
    echo ""
    echo "最少需要配置："
    echo "  - SECRET_KEY (JWT密钥)"
    echo "  - AI_API_KEY (AI服务API密钥)"
    echo ""
    echo "生成SECRET_KEY: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo ""
    read -p "按Enter继续（将使用默认配置）..." 
fi

# 启动服务器
echo ""
echo "================================================"
echo "   启动FastAPI服务器..."
echo "================================================"
echo ""
echo "访问地址:"
echo "  - 主页: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/api/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "================================================"
echo ""

python main.py

