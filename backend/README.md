# Backend Module - Financial Advisor API

## 📋 模块概述

Backend模块是金融顾问系统的核心API服务，基于FastAPI框架构建，提供用户认证、聊天管理、文件存储等核心功能。

## 🏗️ 架构设计

### 技术栈
- **框架**: FastAPI (Python 3.9+)
- **数据库**: SQLite + SQLAlchemy ORM
- **认证**: JWT + bcrypt
- **文件存储**: 本地文件系统 + 安全哈希
- **API文档**: 自动生成OpenAPI文档

### 目录结构
```
backend/
├── main.py              # 主应用入口和API路由
├── models.py            # 数据库模型定义
├── database.py          # 数据库配置和连接
├── auth.py              # 用户认证和JWT处理
├── file_storage.py      # 文件存储和安全处理
├── security.py          # 安全验证和访问控制
├── config.py            # 配置管理
├── requirements.txt     # Python依赖
├── Dockerfile          # Docker构建文件
└── README.md           # 模块说明文档
```

## 🔧 核心功能

### 1. 用户认证系统
- **用户注册**: 支持用户名、密码和邀请码验证
- **用户登录**: JWT Token认证，30分钟过期
- **密码安全**: bcrypt加密存储
- **会话管理**: 自动Token刷新和验证

### 2. 智能上下文聊天
- **上下文构建**: 智能构建对话上下文（最大10条消息）
- **对话摘要**: 自动生成历史对话摘要
- **消息管理**: 完整的消息存储和检索
- **会话管理**: 多会话支持和历史记录

### 3. 安全文件存储
- **文件上传**: 支持多种文件类型上传
- **安全存储**: SHA256哈希文件名，防止路径遍历
- **访问控制**: 用户数据隔离和权限验证
- **文件管理**: 文件列表、下载和删除功能

### 4. Budget Planner功能
- **预算管理**: 创建、更新、删除预算和预算项目
- **会话类型**: 支持Main Session和Budget Planner Session
- **权限控制**: 基于会话类型的智能权限管理
- **用户资料**: 用户信息管理和个性化服务
- **内部API**: 为Brain服务提供预算数据访问接口

## 📊 数据库模型

### User (用户表)
```python
class User(Base):
    id = Column(String(36), primary_key=True)  # UUID
    username = Column(String(50), unique=True)  # 用户名
    password_hash = Column(String(255))        # 加密密码
    created_at = Column(DateTime)              # 创建时间
    updated_at = Column(DateTime)              # 更新时间
```

### ChatSession (聊天会话表)
```python
class ChatSession(Base):
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey)   # 用户ID
    title = Column(String(200))                # 会话标题
    session_type = Column(String(20))          # 会话类型 ('chat'/'budget')
    created_at = Column(DateTime)              # 创建时间
    updated_at = Column(DateTime)              # 更新时间
```

### ChatMessage (聊天消息表)
```python
class ChatMessage(Base):
    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey) # 会话ID
    role = Column(String(20))                  # 角色(user/assistant)
    content = Column(Text)                     # 消息内容
    created_at = Column(DateTime)              # 创建时间
```

### File (文件表)
```python
class File(Base):
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey)   # 用户ID
    session_id = Column(String(36), ForeignKey) # 会话ID(可选)
    filename = Column(String(255))             # 原始文件名
    secure_filename = Column(String(255))      # 安全文件名
    file_path = Column(String(500))            # 文件路径
    file_size = Column(Integer)                # 文件大小
    file_type = Column(String(100))            # 文件类型
    upload_time = Column(DateTime)             # 上传时间
```

### Budget (预算表)
```python
class Budget(Base):
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey)   # 用户ID
    year = Column(Integer)                     # 年份
    month = Column(Integer)                    # 月份 (NULL表示年度预算)
    budget_type = Column(String(20))           # 预算类型 ('monthly'/'annual')
    total_income = Column(DECIMAL(10,2))       # 总收入
    total_expenses = Column(DECIMAL(10,2))     # 总支出
    savings_goal = Column(DECIMAL(10,2))       # 储蓄目标
    created_at = Column(DateTime)              # 创建时间
    updated_at = Column(DateTime)              # 更新时间
```

### BudgetItem (预算项目表)
```python
class BudgetItem(Base):
    id = Column(String(36), primary_key=True)  # UUID
    budget_id = Column(String(36), ForeignKey) # 预算ID
    category = Column(String(100))             # 项目类别
    item_type = Column(String(20))             # 项目类型 ('income'/'expense')
    planned_amount = Column(DECIMAL(10,2))     # 计划金额
    actual_amount = Column(DECIMAL(10,2))      # 实际金额
    description = Column(Text)                 # 描述
    created_at = Column(DateTime)              # 创建时间
    updated_at = Column(DateTime)              # 更新时间
```

### BudgetSettings (预算设置表)
```python
class BudgetSettings(Base):
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey)   # 用户ID
    show_annual = Column(Boolean)              # 显示年度预算
    show_monthly = Column(Boolean)             # 显示月度预算
    currency = Column(String(10))              # 货币类型
    created_at = Column(DateTime)              # 创建时间
    updated_at = Column(DateTime)              # 更新时间
```

## 🚀 API端点

### 认证相关
```
POST /api/auth/login      # 用户登录
POST /api/auth/register   # 用户注册
GET  /api/auth/me         # 获取当前用户信息
```

### 聊天相关
```
POST /api/chat                    # 发送消息（支持上下文和会话类型）
GET  /api/chat/sessions           # 获取聊天会话列表
GET  /api/chat/sessions/{id}/messages  # 获取会话消息
```

### 预算相关
```
GET    /api/budget                # 获取用户预算列表
POST   /api/budget                # 创建新预算
PUT    /api/budget/{id}           # 更新预算
DELETE /api/budget/{id}           # 删除预算
GET    /api/budget/settings       # 获取预算设置
PUT    /api/budget/settings       # 更新预算设置
```

### 用户资料相关
```
GET    /api/user/profile          # 获取用户资料
PUT    /api/user/profile          # 更新用户资料
```

### 内部API (Brain服务专用)
```
POST   /api/internal/budget       # 创建/更新预算项目
GET    /api/internal/budget       # 获取用户预算数据
```

### 文件相关
```
POST   /api/files/upload          # 上传文件
GET    /api/files                 # 获取文件列表
GET    /api/files/{id}/download   # 下载文件
DELETE /api/files/{id}            # 删除文件
```

### 系统相关
```
GET  /health          # 健康检查
GET  /                # 静态文件服务
```

## 🧠 智能上下文管理

### 上下文构建流程
1. **接收请求**: 获取用户消息和会话ID
2. **查询历史**: 从数据库获取历史消息
3. **构建上下文**: 智能构建包含摘要和最近对话的上下文
4. **转发Brain**: 将完整上下文发送给AI服务
5. **保存消息**: 将用户消息和AI回复保存到数据库

### 上下文结构
```python
context_messages = [
    {
        "role": "system",
        "content": "系统提示...",
        "context_type": "system"
    },
    {
        "role": "system", 
        "content": "对话摘要...",
        "context_type": "summary"
    },
    {
        "role": "user",
        "content": "历史消息...",
        "context_type": "history"
    },
    {
        "role": "user",
        "content": "当前问题...",
        "context_type": "current",
        "is_current": True
    }
]
```

### 上下文长度控制
- **最大长度**: 10条消息（可配置）
- **摘要触发**: 超过5条历史消息时自动生成摘要
- **质量优化**: 过滤重要消息，提高上下文质量

## 🔒 安全特性

### 认证安全
- **JWT Token**: 30分钟过期，自动刷新
- **密码加密**: bcrypt算法，不可逆加密
- **邀请码验证**: 硬编码邀请码"JEFF"

### 文件安全
- **文件名哈希**: SHA256加密，防止信息泄露
- **路径验证**: 防止目录遍历攻击
- **类型限制**: 严格的文件类型和大小限制
- **访问控制**: 用户数据完全隔离

### 数据安全
- **SQL注入防护**: SQLAlchemy ORM自动防护
- **XSS防护**: 输入验证和输出转义
- **CSRF防护**: JWT Token验证
- **数据隔离**: 用户只能访问自己的数据

## 🚀 部署配置

### 环境变量
```bash
BACKEND_PORT=8000                    # 服务端口
BRAIN_SERVICE_URL=http://brain:8001  # Brain服务地址
DATABASE_URL=sqlite:///./data/financial_advisor.db  # 数据库URL
DEBUG=true                           # 调试模式
```

### Docker配置
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 开发模式
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📈 性能优化

### 数据库优化
- **连接池**: SQLAlchemy连接池管理
- **索引优化**: 关键字段添加索引
- **查询优化**: 避免N+1查询问题

### 缓存策略
- **上下文缓存**: 智能上下文缓存机制
- **会话缓存**: 用户会话信息缓存
- **文件缓存**: 文件元数据缓存

### 响应优化
- **异步处理**: FastAPI异步支持
- **批量操作**: 批量数据库操作
- **压缩传输**: Gzip压缩响应

## 🔧 开发指南

### 添加新API端点
1. 在`main.py`中定义路由
2. 创建对应的Pydantic模型
3. 实现业务逻辑
4. 添加错误处理
5. 更新API文档

### 数据库迁移
1. 修改`models.py`中的模型
2. 重启服务自动创建表
3. 手动数据迁移（如需要）

### 测试
```bash
# 运行测试
pytest

# 测试覆盖率
pytest --cov=.

# 性能测试
pytest --benchmark-only
```

## 📚 相关文档
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [JWT认证指南](https://jwt.io/introduction)
- [项目主README](../README.md)
