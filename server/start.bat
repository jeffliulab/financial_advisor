@echo off
REM AI Financial Advisor - Windows启动脚本
REM 
REM 使用方法：双击运行此文件

echo.
echo ================================================
echo    AI Financial Advisor - 后端服务启动
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检测Python版本...
python --version

REM 检查虚拟环境
if not exist "venv" (
    echo.
    echo [2/4] 创建虚拟环境...
    python -m venv venv
    echo     虚拟环境创建成功！
) else (
    echo.
    echo [2/4] 虚拟环境已存在，跳过创建
)

REM 激活虚拟环境
echo.
echo [3/4] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo [4/4] 检查并安装依赖包...
pip install -r requirements.txt --quiet

REM 检查.env文件
if not exist ".env" (
    echo.
    echo ================================================
    echo [警告] 未找到 .env 配置文件！
    echo ================================================
    echo.
    echo 请按以下步骤操作：
    echo 1. 复制 env.example 的内容
    echo 2. 创建 .env 文件
    echo 3. 填写你的API密钥等配置
    echo.
    echo 最少需要配置：
    echo   - SECRET_KEY ^(JWT密钥^)
    echo   - AI_API_KEY ^(AI服务API密钥^)
    echo.
    echo 生成SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
    echo.
    pause
    echo.
    echo 继续启动服务（将使用默认配置）...
    timeout /t 3
)

REM 启动服务器
echo.
echo ================================================
echo    启动FastAPI服务器...
echo ================================================
echo.
echo 访问地址:
echo   - 主页: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo   - 健康检查: http://localhost:8000/api/health
echo.
echo 按 Ctrl+C 停止服务器
echo ================================================
echo.

python main.py

REM 如果服务器异常退出
echo.
echo 服务器已停止
pause

