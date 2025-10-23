"""
Backend Service - Main application entry point.
"""
import logging
import os
import time
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File as FastAPIFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import httpx
from datetime import datetime
from config import BACKEND_PORT, BRAIN_SERVICE_URL, DEBUG
from database import get_db, create_tables
from auth import (
    authenticate_user, create_user, create_access_token, 
    verify_token, get_user_by_username, ACCESS_TOKEN_EXPIRE_MINUTES
)
from models import User, ChatSession, ChatMessage, File, Budget, BudgetItem, BudgetSettings
from pydantic import BaseModel
from typing import Optional, List
from file_storage import save_uploaded_file, get_user_files, delete_file
from security import get_file_with_access_check, verify_file_access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Financial Advisor Backend",
    description="Backend service for Financial Advisor application",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()
    logger.info("Database tables created successfully")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (web frontend)
app.mount("/static", StaticFiles(directory="web"), name="static")

# Context management functions
def build_system_prompt() -> str:
    """构建智能系统提示"""
    return """You are a professional financial advisor AI assistant. 

IMPORTANT CONTEXT INSTRUCTIONS:
1. You will receive messages with different context types:
   - "system": System instructions (like this message)
   - "summary": Summary of previous conversation topics
   - "history": Previous conversation messages for context
   - "current": The CURRENT question/request you need to respond to

2. RESPONSE GUIDELINES:
   - Focus ONLY on the "current" message for your response
   - Use "history" messages only for context and continuity
   - Do NOT repeat answers to historical questions
   - Build upon previous conversation naturally
   - If the current question relates to previous topics, acknowledge the connection

3. CONVERSATION FLOW:
   - Maintain conversation continuity
   - Reference relevant previous points when helpful
   - Keep responses focused on the current question
   - Provide fresh insights, not repetitive information

4. RESPONSE FORMAT:
   - Answer the current question directly
   - Use previous context to enhance your response
   - Maintain a natural conversation flow
   - Be concise but comprehensive

Remember: Your primary task is to answer the CURRENT question while using historical context appropriately."""

def create_conversation_summary(history_messages: List) -> str:
    """创建对话摘要"""
    if not history_messages:
        return "No previous conversation."
    
    # 提取关键话题
    topics = []
    user_questions = []
    
    for msg in history_messages:
        if msg.role == "user" and len(msg.content) > 20:
            user_questions.append(msg.content[:100] + "...")
        elif msg.role == "assistant" and len(msg.content) > 50:
            # 提取关键信息
            content_lower = msg.content.lower()
            if "budget" in content_lower:
                topics.append("budget planning")
            elif "investment" in content_lower:
                topics.append("investment advice")
            elif "debt" in content_lower:
                topics.append("debt management")
            elif "tax" in content_lower:
                topics.append("tax planning")
            elif "retirement" in content_lower:
                topics.append("retirement planning")
    
    # 构建摘要
    summary_parts = []
    if topics:
        summary_parts.append(f"Discussed topics: {', '.join(set(topics))}")
    if user_questions:
        summary_parts.append(f"Previous questions: {len(user_questions)} financial queries")
    
    return " | ".join(summary_parts) if summary_parts else "General financial discussion"

def build_chat_context(
    db: Session, 
    session_id: str, 
    max_messages: int = 10,
    include_summary: bool = True,
    budget_mode: bool = False
) -> List[Dict]:
    """构建聊天上下文"""
    
    # 1. 查询历史消息
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(max_messages + 5).all()
    
    # 2. 构建消息列表
    context = []
    
    # 添加系统提示
    context.append({
        "role": "system",
        "content": build_system_prompt(),
        "context_type": "system"
    })
    
    # 如果是Budget模式，添加Budget数据到上下文
    if budget_mode:
        # 获取session的user_id
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            # 获取用户的Budget数据
            budgets = db.query(Budget).filter(Budget.user_id == session.user_id).all()
            if budgets:
                budget_data = []
                for budget in budgets:
                    items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
                    budget_info = {
                        "type": budget.budget_type,
                        "year": budget.year,
                        "month": budget.month,
                        "total_income": budget.total_income,
                        "total_expenses": budget.total_expenses,
                        "savings_goal": budget.savings_goal,
                        "items": [
                            {
                                "category": item.category,
                                "type": item.item_type,
                                "planned": item.planned_amount,
                                "actual": item.actual_amount,
                                "description": item.description
                            }
                            for item in items
                        ]
                    }
                    budget_data.append(budget_info)
                
                context.append({
                    "role": "system",
                    "content": f"User's Budget Data: {budget_data}",
                    "context_type": "budget_data"
                })
    
    # 3. 添加对话摘要（如果历史消息较多且需要摘要）
    if include_summary and len(messages) > 5:
        summary_messages = messages[5:]  # 除了最近5条
        summary = create_conversation_summary(summary_messages)
        context.append({
            "role": "system",
            "content": f"Previous conversation summary: {summary}",
            "context_type": "summary"
        })
    
    # 4. 添加最近的详细历史对话
    recent_messages = messages[:5]  # 最近5条详细对话
    for msg in reversed(recent_messages):  # 按时间顺序
        context.append({
            "role": msg.role,
            "content": msg.content,
            "context_type": "history",
            "timestamp": msg.created_at.isoformat()
        })
    
    return context

async def update_annual_budget_totals(user_id: str, year: int, db: Session):
    """
    重新设计：年度预算 = 月度预算汇总 + 非月度预算汇总
    """
    try:
        # 1. 更新所有月度预算的计算
        monthly_budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.year == year,
            Budget.is_monthly == True
        ).all()
        
        for monthly_budget in monthly_budgets:
            # 计算月度预算的income和expenses
            monthly_items = db.query(BudgetItem).filter(BudgetItem.budget_id == monthly_budget.id).all()
            
            monthly_income = 0
            monthly_expenses = 0
            
            for item in monthly_items:
                if item.item_type == "income":
                    monthly_income += item.planned_amount
                else:
                    monthly_expenses += item.planned_amount
            
            # 更新月度预算
            monthly_budget.total_income = monthly_income
            monthly_budget.total_expenses = monthly_expenses
            monthly_budget.savings_goal = max(0, monthly_income - monthly_expenses)
            monthly_budget.updated_at = datetime.utcnow()
        
        # 2. 更新所有非月度预算的计算
        non_monthly_budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.year == year,
            Budget.is_monthly == False
        ).all()
        
        for non_monthly_budget in non_monthly_budgets:
            # 计算非月度预算的income和expenses
            non_monthly_items = db.query(BudgetItem).filter(BudgetItem.budget_id == non_monthly_budget.id).all()
            
            non_monthly_income = 0
            non_monthly_expenses = 0
            
            for item in non_monthly_items:
                if item.item_type == "income":
                    non_monthly_income += item.planned_amount
                else:
                    non_monthly_expenses += item.planned_amount
            
            # 更新非月度预算
            non_monthly_budget.total_income = non_monthly_income
            non_monthly_budget.total_expenses = non_monthly_expenses
            non_monthly_budget.savings_goal = max(0, non_monthly_income - non_monthly_expenses)
            non_monthly_budget.updated_at = datetime.utcnow()
        
        # 3. 计算年度预算：月度汇总 + 非月度汇总
        # 月度汇总
        monthly_income_total = sum(budget.total_income for budget in monthly_budgets)
        monthly_expenses_total = sum(budget.total_expenses for budget in monthly_budgets)
        
        # 非月度汇总
        non_monthly_income_total = sum(budget.total_income for budget in non_monthly_budgets)
        non_monthly_expenses_total = sum(budget.total_expenses for budget in non_monthly_budgets)
        
        # 年度总计
        annual_income_total = monthly_income_total + non_monthly_income_total
        annual_expenses_total = monthly_expenses_total + non_monthly_expenses_total
        annual_savings_total = max(0, annual_income_total - annual_expenses_total)
        
        # 4. 获取或创建年度预算（用于显示）
        annual_budget = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.year == year,
            Budget.budget_type == "annual"
        ).first()
        
        if not annual_budget:
            annual_budget = Budget(
                user_id=user_id,
                year=year,
                month=None,
                is_monthly=False,  # 年度预算是非月度的，但用于显示汇总
                budget_type="annual",
                total_income=0,
                total_expenses=0,
                savings_goal=0
            )
            db.add(annual_budget)
            db.flush()  # Get the ID
        
        # 5. 更新年度预算显示
        annual_budget.total_income = annual_income_total
        annual_budget.total_expenses = annual_expenses_total
        annual_budget.savings_goal = annual_savings_total
        annual_budget.updated_at = datetime.utcnow()
        
        # 调试信息
        logger.info(f"Updated annual budget totals: monthly_income=${monthly_income_total}, monthly_expenses=${monthly_expenses_total}, "
                   f"non_monthly_income=${non_monthly_income_total}, non_monthly_expenses=${non_monthly_expenses_total}, "
                   f"total_income=${annual_income_total}, total_expenses=${annual_expenses_total}")
        
        # 提交更改
        db.commit()
        
    except Exception as e:
        logger.error(f"Error updating annual budget totals: {str(e)}")
        db.rollback()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_length: Optional[int] = 10  # 默认10条消息的上下文
    include_summary: Optional[bool] = True  # 是否包含摘要
    budget_mode: Optional[bool] = False  # 是否为预算模式

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str = "success"

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    invite_code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    session_type: Optional[str] = None
    created_at: str
    updated_at: str

# Budget-related models
class BudgetItemRequest(BaseModel):
    category: str
    item_type: str  # 'income' or 'expense'
    planned_amount: float
    actual_amount: Optional[float] = 0.0
    description: Optional[str] = None

class BudgetRequest(BaseModel):
    year: int
    month: Optional[int] = None
    budget_type: str  # 'annual' or 'monthly'
    total_income: Optional[float] = 0.0
    total_expenses: Optional[float] = 0.0
    savings_goal: Optional[float] = 0.0
    items: Optional[List[BudgetItemRequest]] = []

class BudgetResponse(BaseModel):
    id: str
    year: int
    month: Optional[int]
    budget_type: str
    total_income: float
    total_expenses: float
    savings_goal: float
    created_at: str
    updated_at: str
    items: List[Dict]

class BudgetSettingsRequest(BaseModel):
    show_annual: bool = True
    show_monthly: bool = True
    currency: str = "USD"

class BudgetSettingsResponse(BaseModel):
    show_annual: bool
    show_monthly: bool
    currency: str

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.get("/")
async def root():
    """Serve the main web page."""
    return FileResponse("web/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Backend Service",
        "brain_service_url": BRAIN_SERVICE_URL
    }

@app.get("/api/debug/chat-logs")
async def get_chat_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    log_type: Optional[str] = None
):
    """Get recent chat logs for debugging (development only)."""
    try:
        from local_development import is_feature_enabled, chat_logger
        
        if not is_feature_enabled("debug_endpoints"):
            raise HTTPException(status_code=404, detail="Not found")
        
        logs = chat_logger.get_recent_logs(limit=limit, log_type=log_type)
        return {"logs": logs, "count": len(logs)}
    except ImportError:
        raise HTTPException(status_code=404, detail="Development tools not available")
    except Exception as e:
        logger.error(f"Error getting chat logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving logs")

@app.get("/api/debug/log-stats")
async def get_log_stats(
    current_user: User = Depends(get_current_user)
):
    """Get logging statistics (development only)."""
    try:
        from local_development import is_feature_enabled, chat_logger
        
        if not is_feature_enabled("debug_endpoints"):
            raise HTTPException(status_code=404, detail="Not found")
        
        stats = chat_logger.get_log_stats()
        return stats
    except ImportError:
        raise HTTPException(status_code=404, detail="Development tools not available")
    except Exception as e:
        logger.error(f"Error getting log stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving stats")

# Internal API endpoints for Brain service
@app.post("/api/internal/budget", response_model=BudgetResponse)
async def create_budget_internal(
    request: BudgetRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Create a new budget (internal API for Brain service)."""
    try:
        # Get user by ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if budget already exists for this year/month/type
        existing_budget = db.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.year == request.year,
            Budget.month == request.month,
            Budget.budget_type == request.budget_type
        ).first()
        
        if existing_budget:
            # Update existing budget instead of creating new one
            existing_budget.updated_at = datetime.utcnow()
            
                # Update or create budget items
            if request.items:
                # Add new items (don't clear existing ones - cumulative approach)
                for item_data in request.items:
                    # Handle both dict and Pydantic model formats
                    if isinstance(item_data, dict):
                        category = item_data["category"]
                        item_type = item_data["item_type"]
                        planned_amount = item_data["planned_amount"]
                        description = item_data.get("description", "")
                    else:
                        category = item_data.category
                        item_type = item_data.item_type
                        planned_amount = item_data.planned_amount
                        description = item_data.description or ""
                    
                    # Check if item already exists
                    existing_item = db.query(BudgetItem).filter(
                        BudgetItem.budget_id == existing_budget.id,
                        BudgetItem.category == category,
                        BudgetItem.item_type == item_type
                    ).first()
                    
                    if existing_item:
                        # Update existing item
                        existing_item.planned_amount = planned_amount
                        existing_item.description = description
                        existing_item.updated_at = datetime.utcnow()
                    else:
                        # Create new item
                        budget_item = BudgetItem(
                            budget_id=existing_budget.id,
                            category=category,
                            item_type=item_type,
                            planned_amount=planned_amount,
                            actual_amount=0,
                            description=description
                        )
                        db.add(budget_item)
                
                # Commit items first so they can be queried
                db.commit()
                
                # Recalculate totals based on all items
                all_items = db.query(BudgetItem).filter(BudgetItem.budget_id == existing_budget.id).all()
                total_income = sum(item.planned_amount for item in all_items if item.item_type == "income")
                total_expenses = sum(item.planned_amount for item in all_items if item.item_type == "expense")
                savings_goal = max(0, total_income - total_expenses)
                
                # Update budget totals
                existing_budget.total_income = total_income
                existing_budget.total_expenses = total_expenses
                existing_budget.savings_goal = savings_goal
                
                # Update annual budget if this is a monthly budget
                if existing_budget.budget_type == "monthly" and existing_budget.month:
                    await update_annual_budget_totals(user.id, existing_budget.year, db)
            
            db.commit()
            db.refresh(existing_budget)
            
            # Get all items for response
            items = db.query(BudgetItem).filter(BudgetItem.budget_id == existing_budget.id).all()
            
            return BudgetResponse(
                id=existing_budget.id,
                year=existing_budget.year,
                month=existing_budget.month,
                budget_type=existing_budget.budget_type,
                total_income=existing_budget.total_income,
                total_expenses=existing_budget.total_expenses,
                savings_goal=existing_budget.savings_goal,
                created_at=existing_budget.created_at.isoformat(),
                updated_at=existing_budget.updated_at.isoformat(),
                items=[
                    {
                        "id": item.id,
                        "category": item.category,
                        "item_type": item.item_type,
                        "planned_amount": item.planned_amount,
                        "actual_amount": item.actual_amount,
                        "description": item.description
                    }
                    for item in items
                ]
            )
        
        # Create new budget - totals will be calculated from items
        # 根据budget_type设置is_monthly字段
        is_monthly = request.budget_type == "monthly"
        
        budget = Budget(
            user_id=user.id,
            year=request.year,
            month=request.month,
            is_monthly=is_monthly,  # 新增字段
            budget_type=request.budget_type,
            total_income=0,  # Will be calculated from items
            total_expenses=0,  # Will be calculated from items
            savings_goal=0  # Will be calculated from items
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        
            # Add budget items
        if request.items:
            for item_data in request.items:
                # Handle both dict and Pydantic model formats
                if isinstance(item_data, dict):
                    budget_item = BudgetItem(
                        budget_id=budget.id,
                        category=item_data["category"],
                        item_type=item_data["item_type"],
                        planned_amount=item_data["planned_amount"],
                        actual_amount=item_data.get("actual_amount", 0),
                        description=item_data.get("description", "")
                    )
                else:
                    budget_item = BudgetItem(
                        budget_id=budget.id,
                        category=item_data.category,
                        item_type=item_data.item_type,
                        planned_amount=item_data.planned_amount,
                        actual_amount=item_data.actual_amount or 0,
                        description=item_data.description or ""
                    )
                db.add(budget_item)
            
            # Commit items first so they can be queried
            db.commit()
            
            # Calculate totals from items
            all_items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
            total_income = sum(item.planned_amount for item in all_items if item.item_type == "income")
            total_expenses = sum(item.planned_amount for item in all_items if item.item_type == "expense")
            savings_goal = max(0, total_income - total_expenses)
            
            # Update budget totals (only for monthly budgets)
            if budget.is_monthly:
                budget.total_income = total_income
                budget.total_expenses = total_expenses
                budget.savings_goal = savings_goal
            else:
                # For non-monthly budgets, also update totals
                budget.total_income = total_income
                budget.total_expenses = total_expenses
                budget.savings_goal = savings_goal
        
        # Always update annual budget totals for both monthly and non-monthly budgets
        await update_annual_budget_totals(user.id, budget.year, db)
        
        # Refresh the budget object to get the updated totals
        db.refresh(budget)
        
        # For annual budgets (display), update the budget totals from the annual budget
        if budget.budget_type == "annual":
            annual_budget = db.query(Budget).filter(
                Budget.user_id == user.id,
                Budget.year == budget.year,
                Budget.budget_type == "annual"
            ).first()
            if annual_budget:
                # 确保年度预算包含月度+非月度的数据
                budget.total_income = annual_budget.total_income
                budget.total_expenses = annual_budget.total_expenses
                budget.savings_goal = annual_budget.savings_goal
                # Commit the updated budget totals
                db.commit()
                # Refresh the budget object to get the updated totals
                db.refresh(budget)
        
        # Final commit for all changes
        db.commit()
        
        # Get all items for response
        items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
        
        return BudgetResponse(
            id=budget.id,
            year=budget.year,
            month=budget.month,
            budget_type=budget.budget_type,
            total_income=budget.total_income,
            total_expenses=budget.total_expenses,
            savings_goal=budget.savings_goal,
            created_at=budget.created_at.isoformat(),
            updated_at=budget.updated_at.isoformat(),
            items=[
                {
                    "id": item.id,
                    "category": item.category,
                    "item_type": item.item_type,
                    "planned_amount": item.planned_amount,
                    "actual_amount": item.actual_amount,
                    "description": item.description
                }
                for item in items
            ]
        )
        
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating budget")

@app.get("/api/internal/budget")
async def get_budgets_internal(
    user_id: str = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Get user's budgets (internal API for Brain service)."""
    try:
        # Get user by ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get budgets with items
        budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
        
        budget_list = []
        for budget in budgets:
            items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
            
            budget_data = {
                "id": budget.id,
                "year": budget.year,
                "month": budget.month,
                "is_monthly": budget.is_monthly,
                "budget_type": budget.budget_type,
                "total_income": budget.total_income,
                "total_expenses": budget.total_expenses,
                "savings_goal": budget.savings_goal,
                "created_at": budget.created_at.isoformat(),
                "updated_at": budget.updated_at.isoformat(),
                "items": [
                    {
                        "id": item.id,
                        "category": item.category,
                        "item_type": item.item_type,
                        "planned_amount": item.planned_amount,
                        "actual_amount": item.actual_amount,
                        "description": item.description,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat()
                    }
                    for item in items
                ]
            }
            budget_list.append(budget_data)
        
        return {"success": True, "budgets": budget_list}
        
    except Exception as e:
        logger.error(f"Error getting budgets: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting budgets")

# Authentication endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login endpoint."""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """User registration endpoint."""
    # Check invite code
    if request.invite_code != "JEFF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite code"
        )
    
    # Check if user already exists
    if get_user_by_username(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    user = create_user(db, request.username, request.password)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at.isoformat()
    )

# Chat history endpoints
@app.get("/api/chat/sessions", response_model=list[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [
        ChatSessionResponse(
            id=session.id,
            title=session.title,
            session_type=session.session_type,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
        for session in sessions
    ]

@app.get("/api/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a specific chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat endpoint with context management that forwards requests to Brain service and saves chat history."""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create chat session
        session_id = request.session_id
        if not session_id:
            # Create new session
            session_type = "budget" if request.budget_mode else "chat"
            title = "Budget Planner Session" if request.budget_mode else (request.message[:50] + "..." if len(request.message) > 50 else request.message)
            
            session = ChatSession(
                user_id=current_user.id,
                title=title,
                session_type=session_type
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id
        else:
            # Verify session belongs to user
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            ).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Build context for the conversation
        context_messages = []
        if session_id:
            context_messages = build_chat_context(
                db, 
                session_id, 
                max_messages=request.context_length,
                include_summary=request.include_summary,
                budget_mode=request.budget_mode
            )
        else:
            # For new sessions, add system prompt
            context_messages.append({
                "role": "system",
                "content": build_system_prompt(),
                "context_type": "system"
            })
        
        # Add current user message to context
        context_messages.append({
            "role": "user",
            "content": request.message,
            "context_type": "current",
            "is_current": True,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save user message to database
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        
        # Forward request with context to Brain service
        async with httpx.AsyncClient() as client:
            try:
                # Log the request (if enabled)
                try:
                    from local_development import chat_logger
                    chat_logger.log_chat_request(
                        user_id=str(current_user.id),
                        session_id=session_id,
                        request_data={
                            "message": request.message,
                            "budget_mode": request.budget_mode,
                            "context_length": len(context_messages)
                        }
                    )
                except ImportError:
                    pass  # Development tools not available
                
                start_time = time.time()
                # Determine session type based on budget mode
                session_type = "budget_planner_session" if request.budget_mode else "main_session"
                
                response = await client.post(
                    f"{BRAIN_SERVICE_URL}/api/chat",
                    json={
                        "messages": context_messages,
                        "user_id": str(current_user.id),
                        "session_type": session_type
                    },
                    timeout=60.0  # Increased timeout to 60 seconds
                )
                processing_time = time.time() - start_time
                
                response.raise_for_status()
                data = response.json()
                
                # Log the response (if enabled)
                try:
                    from local_development import chat_logger
                    chat_logger.log_chat_response(
                        user_id=str(current_user.id),
                        session_id=session_id,
                        response_data=data,
                        processing_time=processing_time
                    )
                except ImportError:
                    pass  # Development tools not available
                
                # Save AI response
                ai_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=data["response"]
                )
                db.add(ai_message)
                db.commit()
                
                return ChatResponse(
                    response=data["response"],
                    session_id=session_id
                )
                
            except httpx.TimeoutException:
                logger.error("Timeout when calling Brain service")
                try:
                    from local_development import chat_logger
                    chat_logger.log_error(
                        user_id=str(current_user.id),
                        session_id=session_id,
                        error_type="timeout",
                        error_message="AI service timeout",
                        error_details={"timeout_seconds": 60.0}
                    )
                except ImportError:
                    pass  # Development tools not available
                raise HTTPException(status_code=504, detail="AI service timeout")
            except httpx.HTTPStatusError as e:
                logger.error(f"Brain service error: {e.response.status_code}")
                try:
                    from local_development import chat_logger
                    chat_logger.log_error(
                        user_id=str(current_user.id),
                        session_id=session_id,
                        error_type="http_error",
                        error_message=f"Brain service error: {e.response.status_code}",
                        error_details={"status_code": e.response.status_code}
                    )
                except ImportError:
                    pass  # Development tools not available
                raise HTTPException(status_code=502, detail="AI service error")
            except httpx.RequestError as e:
                logger.error(f"Request error: {str(e)}")
                try:
                    from local_development import chat_logger
                    chat_logger.log_error(
                        user_id=str(current_user.id),
                        session_id=session_id,
                        error_type="request_error",
                        error_message=f"Request error: {str(e)}",
                        error_details={"error": str(e)}
                    )
                except ImportError:
                    pass  # Development tools not available
                raise HTTPException(status_code=503, detail="AI service unavailable")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# File upload endpoints
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    session_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file for the current user."""
    try:
        # Read file content
        file_content = await file.read()
        
        # Save file
        file_info = save_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.id,
            session_id=session_id
        )
        
        # Save file record to database
        db_file = File(
            id=file_info['id'],
            user_id=file_info['user_id'],
            session_id=file_info['session_id'],
            filename=file_info['filename'],
            secure_filename=file_info['secure_filename'],
            file_path=file_info['file_path'],
            file_size=file_info['file_size'],
            file_type=file_info['file_type']
        )
        
        db.add(db_file)
        db.commit()
        
        return {
            "id": file_info['id'],
            "filename": file_info['filename'],
            "file_size": file_info['file_size'],
            "file_type": file_info['file_type'],
            "category": file_info['category'],
            "upload_time": db_file.upload_time.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/api/files")
async def get_files(
    session_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get files for the current user."""
    try:
        files = get_user_files(db, current_user.id, session_id)
        return {"files": files}
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get files")

@app.delete("/api/files/{file_id}")
async def delete_user_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file."""
    try:
        # Verify file access
        file_record = verify_file_access(file_id, current_user.id, db)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete from filesystem
        if delete_file(file_record.file_path):
            # Delete from database
            db.delete(file_record)
            db.commit()
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

@app.get("/api/files/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file."""
    try:
        # Get file with access control check
        file_info = get_file_with_access_check(file_id, current_user.id, db)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        
        return FileResponse(
            path=file_info['file_path'],
            filename=file_info['filename'],  # Use original filename for download
            media_type=file_info['file_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download file")

# Budget API endpoints
@app.get("/api/budget", response_model=Dict)
async def get_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for the current user."""
    try:
        budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
        
        budget_list = []
        for budget in budgets:
            items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
            budget_data = {
                "id": budget.id,
                "year": budget.year,
                "month": budget.month,
                "is_monthly": budget.is_monthly,
                "budget_type": budget.budget_type,
                "total_income": budget.total_income,
                "total_expenses": budget.total_expenses,
                "savings_goal": budget.savings_goal,
                "created_at": budget.created_at.isoformat(),
                "updated_at": budget.updated_at.isoformat(),
                "items": [
                    {
                        "id": item.id,
                        "category": item.category,
                        "item_type": item.item_type,
                        "planned_amount": item.planned_amount,
                        "actual_amount": item.actual_amount,
                        "description": item.description
                    }
                    for item in items
                ]
            }
            budget_list.append(budget_data)
        
        return {"success": True, "budgets": budget_list}
        
    except Exception as e:
        logger.error(f"Error getting budgets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get budgets")

@app.post("/api/budget", response_model=BudgetResponse)
async def create_budget(
    request: BudgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget."""
    try:
        # Check if budget already exists for this year/month/type
        existing_budget = db.query(Budget).filter(
            Budget.user_id == current_user.id,
            Budget.year == request.year,
            Budget.month == request.month,
            Budget.budget_type == request.budget_type
        ).first()
        
        if existing_budget:
            raise HTTPException(status_code=400, detail="Budget already exists for this period")
        
        # Create new budget
        budget = Budget(
            user_id=current_user.id,
            year=request.year,
            month=request.month,
            budget_type=request.budget_type,
            total_income=request.total_income,
            total_expenses=request.total_expenses,
            savings_goal=request.savings_goal
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        
        # Add budget items
        for item_data in request.items:
            item = BudgetItem(
                budget_id=budget.id,
                category=item_data.category,
                item_type=item_data.item_type,
                planned_amount=item_data.planned_amount,
                actual_amount=item_data.actual_amount,
                description=item_data.description
            )
            db.add(item)
        
        db.commit()
        
        # Get all items for response
        items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
        
        return BudgetResponse(
            id=budget.id,
            year=budget.year,
            month=budget.month,
            budget_type=budget.budget_type,
            total_income=budget.total_income,
            total_expenses=budget.total_expenses,
            savings_goal=budget.savings_goal,
            created_at=budget.created_at.isoformat(),
            updated_at=budget.updated_at.isoformat(),
            items=[
                {
                    "id": item.id,
                    "category": item.category,
                    "item_type": item.item_type,
                    "planned_amount": item.planned_amount,
                    "actual_amount": item.actual_amount,
                    "description": item.description
                }
                for item in items
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create budget")

@app.put("/api/budget/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: str,
    request: BudgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing budget."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        # Update budget fields
        budget.year = request.year
        budget.month = request.month
        budget.budget_type = request.budget_type
        budget.total_income = request.total_income
        budget.total_expenses = request.total_expenses
        budget.savings_goal = request.savings_goal
        budget.updated_at = datetime.utcnow()
        
        # Delete existing items
        db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).delete()
        
        # Add new items
        for item_data in request.items:
            item = BudgetItem(
                budget_id=budget.id,
                category=item_data.category,
                item_type=item_data.item_type,
                planned_amount=item_data.planned_amount,
                actual_amount=item_data.actual_amount,
                description=item_data.description
            )
            db.add(item)
        
        db.commit()
        db.refresh(budget)
        
        # Get all items for response
        items = db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
        
        return BudgetResponse(
            id=budget.id,
            year=budget.year,
            month=budget.month,
            budget_type=budget.budget_type,
            total_income=budget.total_income,
            total_expenses=budget.total_expenses,
            savings_goal=budget.savings_goal,
            created_at=budget.created_at.isoformat(),
            updated_at=budget.updated_at.isoformat(),
            items=[
                {
                    "id": item.id,
                    "category": item.category,
                    "item_type": item.item_type,
                    "planned_amount": item.planned_amount,
                    "actual_amount": item.actual_amount,
                    "description": item.description
                }
                for item in items
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating budget: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update budget")

@app.delete("/api/budget/{budget_id}")
async def delete_budget(
    budget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a budget."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        # Delete budget items first (cascade should handle this, but being explicit)
        db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).delete()
        
        # Delete budget
        db.delete(budget)
        db.commit()
        
        return {"success": True, "message": "Budget deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting budget: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete budget")

@app.get("/api/budget/settings", response_model=BudgetSettingsResponse)
async def get_budget_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get budget settings for the current user."""
    try:
        settings = db.query(BudgetSettings).filter(
            BudgetSettings.user_id == current_user.id
        ).first()
        
        if not settings:
            # Create default settings
            settings = BudgetSettings(
                user_id=current_user.id,
                show_annual=True,
                show_monthly=True,
                currency="USD"
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return BudgetSettingsResponse(
            show_annual=settings.show_annual,
            show_monthly=settings.show_monthly,
            currency=settings.currency
        )
        
    except Exception as e:
        logger.error(f"Error getting budget settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get budget settings")

@app.put("/api/budget/settings", response_model=BudgetSettingsResponse)
async def update_budget_settings(
    request: BudgetSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update budget settings for the current user."""
    try:
        settings = db.query(BudgetSettings).filter(
            BudgetSettings.user_id == current_user.id
        ).first()
        
        if not settings:
            # Create new settings
            settings = BudgetSettings(
                user_id=current_user.id,
                show_annual=request.show_annual,
                show_monthly=request.show_monthly,
                currency=request.currency
            )
            db.add(settings)
        else:
            # Update existing settings
            settings.show_annual = request.show_annual
            settings.show_monthly = request.show_monthly
            settings.currency = request.currency
            settings.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(settings)
        
        return BudgetSettingsResponse(
            show_annual=settings.show_annual,
            show_monthly=settings.show_monthly,
            currency=settings.currency
        )
        
    except Exception as e:
        logger.error(f"Error updating budget settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update budget settings")

# User Profile API
class UserProfileRequest(BaseModel):
    age: Optional[int] = None
    occupation: Optional[str] = None
    income_level: Optional[str] = None
    financial_goals: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None
    investment_experience: Optional[str] = None
    family_status: Optional[str] = None
    location: Optional[str] = None
    currency_preference: Optional[str] = "USD"

class UserProfileResponse(BaseModel):
    username: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    income_level: Optional[str] = None
    financial_goals: List[str] = []
    risk_tolerance: Optional[str] = None
    investment_experience: Optional[str] = None
    family_status: Optional[str] = None
    location: Optional[str] = None
    currency_preference: str = "USD"

@app.get("/api/user/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile information."""
    try:
        # For now, return basic user info
        # In a real implementation, you would have a separate UserProfile table
        return UserProfileResponse(
            username=current_user.username,
            age=None,
            occupation=None,
            income_level=None,
            financial_goals=[],
            risk_tolerance=None,
            investment_experience=None,
            family_status=None,
            location=None,
            currency_preference="USD"
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user profile")

@app.put("/api/user/profile", response_model=UserProfileResponse)
async def update_user_profile(
    request: UserProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information."""
    try:
        # For now, just return the updated data
        # In a real implementation, you would update a UserProfile table
        return UserProfileResponse(
            username=current_user.username,
            age=request.age,
            occupation=request.occupation,
            income_level=request.income_level,
            financial_goals=request.financial_goals or [],
            risk_tolerance=request.risk_tolerance,
            investment_experience=request.investment_experience,
            family_status=request.family_status,
            location=request.location,
            currency_preference=request.currency_preference or "USD"
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user profile")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=DEBUG,
        log_level="info"
    )