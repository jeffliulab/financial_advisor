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

6. GET /api/budget/dashboard  [需要认证]
   输入: year, Authorization Header
   输出: {year, total_income, total_expense, total_surplus, ...}

7. GET /api/budget/items  [需要认证]
   输入: year, months?, Authorization Header
   输出: {income_items: [...], expense_items: [...]}

8. POST /api/budget/items  [需要认证]
   输入: {name, scope, time_type, category, amount}, Authorization Header
   输出: {success, message, item_id}

9. PUT /api/budget/items/{item_id}  [需要认证]
   输入: {name?, scope?, time_type?, category?, amount?}, Authorization Header
   输出: {success, message, item}

10. DELETE /api/budget/items/{item_id}  [需要认证]
    输入: item_id, Authorization Header
    输出: {success, message}

11. GET /api/budget/info  [需要认证]
    输入: year?, Authorization Header
    输出: {items: [...], available_years: [...]}

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
  - brain/tools/budget_planner.py (预算规划)

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

# 导入budget planner模块
import sys
from pathlib import Path
brain_tools_path = Path(__file__).parent.parent / "brain" / "tools"
sys.path.insert(0, str(brain_tools_path))

try:
    from budget_planner import (
        get_user_budget_info,
        add_budget_item,
        update_budget_item,
        delete_budget_item,
        calculate_dashboard,
        get_items_by_month
    )
    BUDGET_PLANNER_AVAILABLE = True
except ImportError:
    BUDGET_PLANNER_AVAILABLE = False
    print("⚠️  Warning: Budget Planner module not available")


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
#                               Budget Planner API
# ============================================================================

class BudgetItemRequest(BaseModel):
    """添加预算项目请求"""
    name: str
    scope: str  # "永久" 或 "2025年12月" 或 "2025年"
    time_type: str  # "月度" 或 "非月度"
    category: str  # "收入" 或 "支出"
    amount: float


class BudgetItemUpdateRequest(BaseModel):
    """更新预算项目请求"""
    name: Optional[str] = None
    scope: Optional[str] = None
    time_type: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None


@app.get("/api/budget/dashboard", tags=["预算规划"])
async def get_budget_dashboard(
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定年份的Dashboard统计数据
    
    Args:
        year: 年份
        current_user: 当前用户
        
    Returns:
        dict: Dashboard统计数据
    """
    if not BUDGET_PLANNER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Budget Planner service not available"
        )
    
    username = current_user["username"]
    
    try:
        dashboard_data = calculate_dashboard(username, year)
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate dashboard: {str(e)}"
        )


@app.get("/api/budget/items", tags=["预算规划"])
async def get_budget_items(
    year: int,
    months: Optional[str] = "all",
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定年份和月份的预算项目
    
    Args:
        year: 年份
        months: 月份列表（逗号分隔，如 "1,2,3"），"all" 表示所有月份
        current_user: 当前用户
        
    Returns:
        dict: 预算项目列表
    """
    if not BUDGET_PLANNER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Budget Planner service not available"
        )
    
    username = current_user["username"]
    
    # 解析月份参数
    month_list = None
    if months != "all":
        try:
            month_list = [int(m.strip()) for m in months.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid months parameter"
            )
    
    try:
        items_data = get_items_by_month(username, year, month_list)
        return items_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get items: {str(e)}"
        )


@app.post("/api/budget/items", tags=["预算规划"])
async def add_budget_item_api(
    request: BudgetItemRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加预算项目
    
    Args:
        request: 预算项目数据
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    if not BUDGET_PLANNER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Budget Planner service not available"
        )
    
    username = current_user["username"]
    
    # 构建项目数据
    item = {
        "name": request.name,
        "scope": request.scope,
        "time_type": request.time_type,
        "category": request.category,
        "amount": request.amount
    }
    
    try:
        result = add_budget_item(username, item)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add item: {str(e)}"
        )


@app.delete("/api/budget/items/{item_id}", tags=["预算规划"])
async def delete_budget_item_api(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除预算项目
    
    Args:
        item_id: 项目ID
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    if not BUDGET_PLANNER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Budget Planner service not available"
        )
    
    username = current_user["username"]
    
    try:
        result = delete_budget_item(username, item_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )


@app.put("/api/budget/items/{item_id}", tags=["预算规划"])
async def update_budget_item_api(
    item_id: str,
    request: BudgetItemUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新预算项目
    
    Args:
        item_id: 项目ID
        request: 更新的预算项目数据
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    if not BUDGET_PLANNER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Budget Planner service not available"
        )
    
    username = current_user["username"]
    
    # 构建更新数据（只包含非None的字段）
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.scope is not None:
        updates["scope"] = request.scope
    if request.time_type is not None:
        updates["time_type"] = request.time_type
    if request.category is not None:
        updates["category"] = request.category
    if request.amount is not None:
        updates["amount"] = request.amount
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        result = update_budget_item(username, item_id, updates)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@app.get("/api/budget/info", tags=["预算规划"])
async def get_budget_info(
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的预算信息（包含所有项目和可用年份）
    
    Args:
        year: 年份（可选）
        current_user: 当前用户
        
    Returns:
        dict: 预算信息
    """
    if not BUDGET_PLANNER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Budget Planner service not available"
        )
    
    username = current_user["username"]
    
    try:
        budget_info = get_user_budget_info(username, year)
        return budget_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget info: {str(e)}"
        )


# ============================================================================
#                               UI动态控制系统
# ============================================================================

# 全局命令队列（生产环境应使用Redis等持久化方案）
ui_command_queue = []
current_ui_state = {
    "dashboard_active": False,
    "current_tool": None,
    "layout_mode": "two-column"
}

class UICommandRequest(BaseModel):
    """UI命令请求"""
    command: str
    params: dict = {}

class UIEventRequest(BaseModel):
    """UI事件请求（前端按钮点击等）"""
    event_type: str
    event_data: dict = {}

@app.post("/api/ui/command", tags=["UI控制"])
async def send_ui_command(request: UICommandRequest):
    """
    发送UI控制命令（无需认证，供Agent/脚本调用）
    
    来自后端的命令会生成到队列，供前端轮询执行
    
    Args:
        request: UI命令请求
        
    Returns:
        dict: 命令结果
    """
    import uuid
    from datetime import datetime
    
    # 验证命令类型
    valid_commands = ["open_dashboard", "close_dashboard", "switch_session"]
    if request.command not in valid_commands:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid command. Valid commands: {valid_commands}"
        )
    
    # 生成命令ID
    command_id = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    # 构建命令对象
    command = {
        "command": request.command,
        "params": request.params,
        "timestamp": datetime.now().isoformat(),
        "command_id": command_id,
        "source": "backend"  # 标记来源：后端
    }
    
    # 加入命令队列（后端触发，需要前端执行）
    ui_command_queue.append(command)
    
    # 更新状态
    if request.command == "open_dashboard" and "tool" in request.params:
        current_ui_state["dashboard_active"] = True
        current_ui_state["current_tool"] = request.params["tool"]
        current_ui_state["layout_mode"] = "three-column"
    elif request.command == "close_dashboard":
        current_ui_state["dashboard_active"] = False
        current_ui_state["current_tool"] = None
        current_ui_state["layout_mode"] = "two-column"
    
    return {
        "success": True,
        "message": "Command queued successfully",
        "command_id": command_id,
        "source": "backend"
    }


@app.post("/api/ui/event", tags=["UI控制"])
async def handle_ui_event(request: UIEventRequest):
    """
    处理前端UI事件（按钮点击等）
    
    前端发送事件 -> 后端处理 -> 生成UI命令 -> 前端轮询执行
    
    Args:
        request: UI事件请求
        
    Returns:
        dict: 处理结果
    """
    import uuid
    from datetime import datetime
    
    event_type = request.event_type
    event_data = request.event_data
    
    # 事件处理逻辑
    command = None
    
    if event_type == "button_click":
        button_id = event_data.get("button_id")
        
        # 根据按钮ID生成对应的UI命令
        if button_id == "budget-planner":
            command = {
                "command": "open_dashboard",
                "params": {"tool": "budget-planner"}
            }
        elif button_id == "spending-analyzer":
            command = {
                "command": "open_dashboard",
                "params": {"tool": "spending-analyzer"}
            }
        elif button_id == "investment-dashboard":
            command = {
                "command": "open_dashboard",
                "params": {"tool": "investment-dashboard"}
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown button_id: {button_id}"
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown event_type: {event_type}"
        )
    
    # 如果生成了命令，加入队列
    if command:
        command_id = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        command["timestamp"] = datetime.now().isoformat()
        command["command_id"] = command_id
        command["source"] = "ui_event"
        
        ui_command_queue.append(command)
        
        # 更新状态
        if command["command"] == "open_dashboard" and "tool" in command["params"]:
            current_ui_state["dashboard_active"] = True
            current_ui_state["current_tool"] = command["params"]["tool"]
            current_ui_state["layout_mode"] = "three-column"
        
        return {
            "success": True,
            "message": "Event processed and command queued",
            "command_id": command_id,
            "command": command["command"]
        }
    
    return {
        "success": False,
        "message": "Event processed but no command generated"
    }


@app.get("/api/ui/state", tags=["UI控制"])
async def get_ui_state():
    """
    获取当前UI状态和待执行命令（前端轮询）
    
    Returns:
        dict: UI状态和命令队列
    """
    # 返回队列中的所有待执行命令
    pending = ui_command_queue.copy()
    
    # 清空队列（命令被前端获取后即删除）
    ui_command_queue.clear()
    
    return {
        "pending_commands": pending,
        "current_state": current_ui_state
    }


class StateSyncRequest(BaseModel):
    """状态同步请求"""
    dashboard_active: bool = None
    current_tool: str = None
    layout_mode: str = None
    source: str = "frontend"  # frontend 或 backend


@app.post("/api/ui/state/sync", tags=["UI控制"])
async def sync_ui_state(request: StateSyncRequest):
    """
    前端同步UI状态到后端
    
    用于前端立即响应场景（按钮点击）：
    - 前端立即切换布局（0延迟）
    - 同步状态到后端（source: frontend）
    - 后端只记录状态，不生成命令（避免重复执行）
    
    Args:
        request: 状态同步请求
        
    Returns:
        dict: 同步结果
    """
    global current_ui_state
    
    # 更新状态（只更新非None的字段）
    if request.dashboard_active is not None:
        current_ui_state["dashboard_active"] = request.dashboard_active
    if request.current_tool is not None:
        current_ui_state["current_tool"] = request.current_tool
    if request.layout_mode is not None:
        current_ui_state["layout_mode"] = request.layout_mode
    
    # 关键：如果来自前端，不生成命令（前端已经执行了）
    # 如果来自后端，这里也不应该调用（应该用 /api/ui/command）
    
    return {
        "success": True,
        "message": "State synced (no command generated)",
        "current_state": current_ui_state,
        "source": request.source
    }


# ============================================================================
#                       Dashboard端点（已废弃，保留兼容）
# ============================================================================

class DashboardRequest(BaseModel):
    """Dashboard激活请求（已废弃）"""
    tool: str

@app.post("/api/dashboard/activate", tags=["Dashboard (已废弃)"])
async def activate_dashboard(
    request: DashboardRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    激活Dashboard工具面板（已废弃）
    
    ⚠️ 此接口已废弃，请使用 POST /api/ui/command 或 POST /api/ui/event
    
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
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    print("=" * 60)
    print("AI Financial Advisor API Server")
    print("Powered by DeepSeek AI")
    print("Starting...")
    print("=" * 60)
    
    # 显示配置信息
    print("\nDeepSeek API Configuration:")
    ai_config = chat.get_ai_config()
    print(f"   API Base URL: {ai_config['api_base_url']}")
    print(f"   Model: {ai_config['model']}")
    print(f"   Temperature: {ai_config['temperature']}")
    print(f"   Max Tokens: {ai_config['max_tokens']}")
    print(f"   API Key: {'Configured' if ai_config['api_key_configured'] else 'Not Configured'}")
    
    # 测试DeepSeek连接
    print("\nTesting DeepSeek API Connection...")
    test_result = chat.test_ai_connection()
    if test_result['success']:
        print(f"   Success: {test_result['message']}")
    else:
        print(f"   Failed: {test_result['message']}")
        print("\nWarning: DeepSeek API not properly configured, chat functionality may not work")
        print("   Please set the following environment variables in .env file:")
        print("   - DEEPSEEK_API_KEY: Your DeepSeek API key")
        print("   - DEEPSEEK_BASE_URL: API base URL (optional, usually no need to modify)")
        print("   - DEEPSEEK_MODEL: Model name (optional, usually no need to modify)")
        print("\n   Get API key: https://platform.deepseek.com/")
    
    print("\nServer Starting...")
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

