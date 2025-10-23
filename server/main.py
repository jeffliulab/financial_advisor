"""
═══════════════════════════════════════════════════════════════════════════
main.py - FastAPI 主服务入口
═══════════════════════════════════════════════════════════════════════════

【API端点】

1. POST /api/auth/login
   输入: {username, password}
   输出: {access_token, user_id, username}

2. POST /api/auth/register
   输入: {username, password, invite_code}
   输出: {access_token, user_id, username}

3. POST /api/chat  [需要认证]
   输入: {message, session_id?, context_length?, include_summary?}
   输出: {response, session_id, message_id, timestamp}

4. GET /api/chat/sessions  [需要认证]
   输入: Authorization Header
   输出: [{id, title, created_at, updated_at, message_count}, ...]

5. GET /api/chat/sessions/{session_id}/messages  [需要认证]
   输入: session_id, Authorization Header
   输出: [{id, role, content, created_at, session_id}, ...]

【功能模块】
  - FastAPI路由和中间件
  - JWT Token认证
  - CORS跨域支持
  - 静态文件服务 (web/)
  - 自动API文档 (/docs)

【依赖模块】
  - auth.py (用户认证)
  - register.py (用户注册)
  - chat.py (AI对话)
  - chat_history.py (历史管理)

【启动方式】
  python main.py
  或: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
═══════════════════════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from pathlib import Path

# 导入自定义模块
import auth
import register
import chat
import chat_history


# ============================================================================
#                               FastAPI 应用初始化
# ============================================================================

app = FastAPI(
    title="AI Financial Advisor API",
    description="AI财务顾问后端服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Bearer认证
security = HTTPBearer()


# ============================================================================
#                               数据模型 (Pydantic Models)
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    invite_code: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_length: Optional[int] = 10
    include_summary: Optional[bool] = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user_id: int
    username: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: int
    timestamp: str


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class MessageInfo(BaseModel):
    id: int
    role: str
    content: str
    created_at: str
    session_id: str


# ============================================================================
#                               认证依赖
# ============================================================================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    从Token获取当前用户（依赖注入）
    
    Args:
        credentials: HTTP认证凭证
        
    Returns:
        dict: 用户信息
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    token = credentials.credentials
    user = auth.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# ============================================================================
#                               API端点 - 认证
# ============================================================================

@app.post("/api/auth/login", response_model=LoginResponse, tags=["认证"])
async def login(request: LoginRequest):
    """
    用户登录
    
    Args:
        request: 登录请求（用户名和密码）
        
    Returns:
        LoginResponse: 登录响应（包含token和用户信息）
        
    Raises:
        HTTPException: 登录失败时抛出401错误
    """
    # 验证用户
    user = auth.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or Password INCORRECT",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成token
    access_token = auth.create_access_token(
        data={"sub": user["username"], "user_id": user["user_id"]}
    )
    
    return LoginResponse(
        access_token=access_token,
        user_id=user["user_id"],
        username=user["username"]
    )


@app.post("/api/auth/register", response_model=LoginResponse, tags=["认证"])
async def register_user(request: RegisterRequest):
    """
    用户注册
    
    Args:
        request: 注册请求（用户名、密码、邀请码）
        
    Returns:
        LoginResponse: 注册响应（包含token和用户信息）
        
    Raises:
        HTTPException: 注册失败时抛出400错误
    """
    # 注册用户
    result = register.register_user(
        request.username,
        request.password,
        request.invite_code
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return LoginResponse(
        access_token=result["access_token"],
        user_id=result["user_data"]["user_id"],
        username=result["user_data"]["username"]
    )


# ============================================================================
#                               API端点 - 聊天
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse, tags=["聊天"])
async def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发送聊天消息
    
    Args:
        request: 聊天请求
        current_user: 当前用户（从token自动获取）
        
    Returns:
        ChatResponse: 聊天响应（包含AI回复和会话信息）
        
    Raises:
        HTTPException: 处理失败时抛出500错误
    """
    username = current_user["username"]
    
    # 1. 确定会话ID
    if request.session_id:
        # 使用现有会话
        session_id = request.session_id
        if not chat_history.session_exists(username, session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    else:
        # 创建新会话
        session = chat_history.create_session(username, request.message)
        session_id = session["id"]
    
    # 2. 保存用户消息
    user_message = chat_history.add_message(
        username,
        session_id,
        "user",
        request.message
    )
    
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save user message"
        )
    
    # 3. 获取对话上下文
    context_messages = []
    if request.context_length and request.context_length > 0:
        context_messages = chat_history.build_conversation_context(
            username,
            session_id,
            request.context_length
        )
    
    # 4. 调用AI生成回复
    ai_response = chat.generate_response(
        request.message,
        context_messages
    )
    
    if not ai_response["success"]:
        # AI调用失败，但仍然保存错误消息
        error_message = f"抱歉，我遇到了一些问题：{ai_response['error']}"
        assistant_message = chat_history.add_message(
            username,
            session_id,
            "assistant",
            error_message
        )
        
        return ChatResponse(
            response=error_message,
            session_id=session_id,
            message_id=assistant_message["id"],
            timestamp=assistant_message["created_at"]
        )
    
    # 5. 保存AI回复
    assistant_message = chat_history.add_message(
        username,
        session_id,
        "assistant",
        ai_response["response"]
    )
    
    if not assistant_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save assistant message"
        )
    
    # 6. 返回响应
    return ChatResponse(
        response=ai_response["response"],
        session_id=session_id,
        message_id=assistant_message["id"],
        timestamp=assistant_message["created_at"]
    )


@app.get("/api/chat/sessions", response_model=List[SessionInfo], tags=["聊天"])
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """
    获取用户所有会话列表
    
    Args:
        current_user: 当前用户（从token自动获取）
        
    Returns:
        List[SessionInfo]: 会话列表
    """
    username = current_user["username"]
    sessions = chat_history.get_all_sessions(username)
    
    return [SessionInfo(**session) for session in sessions]


@app.get("/api/chat/sessions/{session_id}/messages", response_model=List[MessageInfo], tags=["聊天"])
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定会话的所有消息
    
    Args:
        session_id: 会话ID
        current_user: 当前用户（从token自动获取）
        
    Returns:
        List[MessageInfo]: 消息列表
        
    Raises:
        HTTPException: 会话不存在时抛出404错误
    """
    username = current_user["username"]
    
    # 检查会话是否存在
    if not chat_history.session_exists(username, session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # 获取消息
    messages = chat_history.get_messages(username, session_id)
    
    return [MessageInfo(**message) for message in messages]


# ============================================================================
#                               API端点 - 健康检查
# ============================================================================

@app.get("/api/health", tags=["系统"])
async def health_check():
    """
    健康检查
    
    Returns:
        dict: 服务状态
    """
    return {
        "status": "healthy",
        "service": "AI Financial Advisor API",
        "version": "1.0.0"
    }


@app.get("/api/config", tags=["系统"])
async def get_config(current_user: dict = Depends(get_current_user)):
    """
    获取AI配置信息（需要认证）
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 配置信息
    """
    return chat.get_ai_config()


# ============================================================================
#                               Dashboard端点
# ============================================================================

class DashboardRequest(BaseModel):
    """Dashboard激活请求"""
    tool: str

@app.post("/api/dashboard/activate", tags=["Dashboard"])
async def activate_dashboard(
    request: DashboardRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    激活Dashboard工具面板
    
    Args:
        request: Dashboard请求（工具名称）
        current_user: 当前用户（从token自动获取）
        
    Returns:
        dict: Dashboard配置信息
    """
    # 工具映射配置
    tool_config = {
        "budget-planner": {
            "title": "Budget Planner",
            "url": "/tools/budget-planner.html"
        },
        "spending-analyzer": {
            "title": "Spending Analyzer", 
            "url": "/tools/spending-analyzer.html"
        },
        "investment-dashboard": {
            "title": "Investment Dashboard",
            "url": "/tools/coming-soon.html"
        }
    }
    
    tool_name = request.tool
    
    if tool_name not in tool_config:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tool: {tool_name}"
        )
    
    config = tool_config[tool_name]
    
    return {
        "dashboard_active": True,
        "tool_name": tool_name,
        "tool_title": config["title"],
        "tool_url": config["url"]
    }


# ============================================================================
#                               静态文件服务
# ============================================================================

# 挂载web静态文件目录
if Path("web").exists():
    app.mount("/web", StaticFiles(directory="web"), name="web")

# 挂载tools静态文件目录
if Path("web/tools").exists():
    app.mount("/tools", StaticFiles(directory="web/tools"), name="tools")


@app.get("/", tags=["页面"])
async def serve_index():
    """
    提供主页面
    
    Returns:
        FileResponse: index.html文件
    """
    index_file = Path("web/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {"message": "Welcome to AI Financial Advisor API"}


# ============================================================================
#                               启动函数
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         AI Financial Advisor API Server                     ║
    ║              Powered by DeepSeek AI                          ║
    ║                     Starting...                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 显示配置信息
    print("📋 DeepSeek API Configuration:")
    ai_config = chat.get_ai_config()
    print(f"   API Base URL: {ai_config['api_base_url']}")
    print(f"   Model: {ai_config['model']}")
    print(f"   Temperature: {ai_config['temperature']}")
    print(f"   Max Tokens: {ai_config['max_tokens']}")
    print(f"   API Key: {'Configured ✓' if ai_config['api_key_configured'] else 'Not Configured ✗'}")
    
    # 测试DeepSeek连接
    print("\n🔌 Testing DeepSeek API Connection...")
    test_result = chat.test_ai_connection()
    if test_result['success']:
        print(f"   ✓ {test_result['message']}")
    else:
        print(f"   ✗ {test_result['message']}")
        print("\n⚠️  Warning: DeepSeek API not properly configured, chat functionality may not work")
        print("   Please set the following environment variables in .env file:")
        print("   - DEEPSEEK_API_KEY: Your DeepSeek API key")
        print("   - DEEPSEEK_BASE_URL: API base URL (optional, usually no need to modify)")
        print("   - DEEPSEEK_MODEL: Model name (optional, usually no need to modify)")
        print("\n   Get API key: https://platform.deepseek.com/")
    
    print("\n🚀 Server Starting...")
    print("   Access URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Frontend: http://localhost:8000/")
    print("\nPress Ctrl+C to stop the server\n")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式，文件修改自动重载
        log_level="info"
    )

