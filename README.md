# Financial Advisor - Simple Architecture

## 📋 项目概述

这是一个简化的金融顾问AI聊天系统，采用微服务架构，包含**完整的用户认证系统**、**智能上下文管理**、**聊天历史管理**和**企业级安全文件存储**功能。

※ 注意：如果实际投产使用，需要用私有云来保护用户数据安全性

### 🧠 核心功能

- **智能上下文管理**: AI能够记住对话历史，提供连贯的智能回复
- **用户认证系统**: 完整的登录/注册功能，支持邀请码验证
- **聊天历史管理**: 支持多会话管理，最近聊天和完整历史查看
- **安全文件存储**: 企业级文件上传和管理功能
- **响应式界面**: 现代化的聊天界面，支持侧边栏和滚动功能
- **Budget Planner**: 智能预算规划工具，支持预算创建、修改和分析
- **会话类型权限**: 基于会话类型的智能权限管理系统
- **用户资料库**: 完整的用户信息管理和个性化服务

### 🔒 安全特性

- **密码加密**: 使用bcrypt算法加密存储用户密码，确保密码安全
- **JWT认证**: 采用JWT Token进行用户身份验证，30分钟自动过期
- **文件安全**: 实现企业级文件存储安全机制，文件名哈希加密，路径安全验证
- **数据隔离**: 用户数据完全隔离，只能访问自己的聊天记录和文件
- **访问控制**: 多层访问控制验证，防止未授权访问

### 🎯 智能上下文特性

- **上下文长度控制**: 最大10条消息的智能上下文管理
- **对话摘要功能**: 自动生成历史对话摘要，保持关键信息
- **消息类型识别**: 智能区分系统提示、历史对话、摘要和当前问题
- **AI响应优化**: AI能够基于上下文提供更智能和连贯的回答
- **性能优化**: 避免token超限，保持快速响应

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Backend API   │    │   Brain AI      │
│   (HTML/JS)     │◄──►│   (FastAPI)     │◄──►│   (LangGraph)   │
│   Port: 8000    │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   SQLite DB     │              │
         │              │   + File Store  │              │
         │              │   + Budget Data │              │
         │              │   + User Profile│              │
         │              └─────────────────┘              │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │  Security Layer │              │
         │              │  ┌─────────────┐│              │
         │              │  │ bcrypt      ││              │
         │              │  │ JWT Auth    ││              │
         │              │  │ File Hash   ││              │
         │              │  │ Access Ctrl ││              │
         │              │  │ Permissions ││              │
         │              │  └─────────────┘│              │
         │              └─────────────────┘              │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │  Session Types  │              │
         │              │  ┌─────────────┐│              │
         │              │  │ Main Session││              │
         │              │  │ Budget Mode ││              │
         │              │  │ Permissions ││              │
         │              │  └─────────────┘│              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │    │  Budget Planner │    │  AI Permissions │
│                 │    │  Dashboard      │    │  Management     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔐 安全架构组件

#### 加密与认证层

- **bcrypt密码加密**: 用户密码使用bcrypt算法加密存储，不可逆加密
- **JWT Token认证**: 用户身份验证采用JWT Token，自动过期机制
- **文件哈希加密**: 上传文件名使用SHA256哈希加密，隐藏原始信息
- **访问控制验证**: 多层验证确保用户只能访问自己的数据

### 服务组件

#### 1. **Web Frontend** (`web/index.html`)

- **技术栈**: HTML5 + CSS3 + JavaScript (Vanilla)
- **功能**:
  - 用户认证界面（登录/注册）
  - 聊天界面（支持Markdown渲染）
  - 侧边栏（聊天历史、快速操作）
  - 响应式设计
- **端口**: 8000 (通过Backend服务)

#### 2. **Backend API** (`backend/`)

- **技术栈**: FastAPI + SQLAlchemy + PyJWT + bcrypt
- **功能**:
  - 用户认证和授权
  - 聊天会话管理
  - 文件上传/下载
  - 数据库操作
  - 静态文件服务
- **端口**: 8000

#### 3. **Brain AI Service** (`brain/`)

- **技术栈**: FastAPI + LangGraph + DeepSeek API + 权限管理
- **功能**:
  - AI对话处理（基于会话类型）
  - LangGraph工作流（智能路由）
  - DeepSeek API集成
  - 权限管理系统
  - 用户资料库管理
  - 预算数据管理
  - 会话类型识别和路由
- **端口**: 8001

## 🗄️ 数据库设计

### 数据库类型

- **SQLite** (轻量级，适合开发和小型应用)
- **位置**: `./backend_data/financial_advisor.db`
- **持久化**: Docker卷挂载

### 数据表结构

#### 用户表 (users)

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    username VARCHAR(50) UNIQUE NOT NULL, -- 用户名
    password_hash VARCHAR(255) NOT NULL,  -- 密码哈希
    created_at DATETIME DEFAULT NOW(),    -- 创建时间
    updated_at DATETIME DEFAULT NOW()     -- 更新时间
);
```

#### 聊天会话表 (chat_sessions)

```sql
CREATE TABLE chat_sessions (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- 用户ID (外键)
    title VARCHAR(200) NOT NULL,          -- 会话标题
    session_type VARCHAR(20) DEFAULT 'chat', -- 会话类型 ('chat'/'budget')
    created_at DATETIME DEFAULT NOW(),    -- 创建时间
    updated_at DATETIME DEFAULT NOW(),    -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 聊天消息表 (chat_messages)

```sql
CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    session_id VARCHAR(36) NOT NULL,      -- 会话ID (外键)
    role VARCHAR(20) NOT NULL,            -- 消息角色 ('user'/'assistant')
    content TEXT NOT NULL,                -- 消息内容
    created_at DATETIME DEFAULT NOW(),    -- 创建时间
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

#### 文件表 (files)

```sql
CREATE TABLE files (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- 用户ID (外键)
    session_id VARCHAR(36),               -- 会话ID (外键，可选)
    filename VARCHAR(255) NOT NULL,       -- 原始文件名
    secure_filename VARCHAR(255) NOT NULL, -- 安全文件名
    file_path VARCHAR(500) NOT NULL,      -- 文件路径
    file_size INTEGER NOT NULL,           -- 文件大小
    file_type VARCHAR(100) NOT NULL,      -- MIME类型
    upload_time DATETIME DEFAULT NOW(),   -- 上传时间
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

#### 预算表 (budgets)

```sql
CREATE TABLE budgets (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- 用户ID (外键)
    year INTEGER NOT NULL,                -- 年份
    month INTEGER,                        -- 月份 (NULL表示年度预算)
    budget_type VARCHAR(20) NOT NULL,     -- 预算类型 ('monthly'/'annual')
    total_income DECIMAL(10,2) DEFAULT 0, -- 总收入
    total_expenses DECIMAL(10,2) DEFAULT 0, -- 总支出
    savings_goal DECIMAL(10,2) DEFAULT 0, -- 储蓄目标
    created_at DATETIME DEFAULT NOW(),    -- 创建时间
    updated_at DATETIME DEFAULT NOW(),    -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 预算项目表 (budget_items)

```sql
CREATE TABLE budget_items (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    budget_id VARCHAR(36) NOT NULL,       -- 预算ID (外键)
    category VARCHAR(100) NOT NULL,       -- 项目类别
    item_type VARCHAR(20) NOT NULL,       -- 项目类型 ('income'/'expense')
    planned_amount DECIMAL(10,2) NOT NULL, -- 计划金额
    actual_amount DECIMAL(10,2) DEFAULT 0, -- 实际金额
    description TEXT,                     -- 描述
    created_at DATETIME DEFAULT NOW(),    -- 创建时间
    updated_at DATETIME DEFAULT NOW(),    -- 更新时间
    FOREIGN KEY (budget_id) REFERENCES budgets(id)
);
```

#### 预算设置表 (budget_settings)

```sql
CREATE TABLE budget_settings (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- 用户ID (外键)
    show_annual BOOLEAN DEFAULT TRUE,     -- 显示年度预算
    show_monthly BOOLEAN DEFAULT TRUE,    -- 显示月度预算
    currency VARCHAR(10) DEFAULT 'USD',   -- 货币类型
    created_at DATETIME DEFAULT NOW(),    -- 创建时间
    updated_at DATETIME DEFAULT NOW(),    -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🔐 用户认证系统

### 认证流程

- **JWT Token** 认证（30分钟有效期，自动过期保护）
- **bcrypt** 密码加密存储（不可逆加密，企业级安全标准）
- **localStorage** 前端状态保存（本地存储，支持自动登录）

### 🔒 加密安全机制

- **密码加密**: 使用bcrypt算法，salt值随机生成，防止彩虹表攻击
- **Token安全**: JWT签名验证，防止Token伪造和篡改
- **会话管理**: 自动过期机制，防止长期会话劫持
- **数据隔离**: 用户数据完全隔离，确保隐私安全

### 注册流程

```
用户输入 → 验证邀请码("JEFF") → 检查用户名唯一性 → 密码加密 → 创建用户 → 生成JWT → 自动登录
```

### 登录流程

```
用户输入 → 验证用户名密码 → 生成JWT → 返回用户信息 → 前端保存状态
```

### API端点

```
POST /api/auth/login      # 用户登录
POST /api/auth/register   # 用户注册
GET  /api/auth/me         # 获取当前用户信息
```

## 📁 安全文件存储系统

### 安全特性

#### 1. 文件名安全（企业级加密）

- 使用 `SHA256` 哈希算法生成安全文件名
- 结合时间戳和UUID随机数确保唯一性
- 原始文件名仅存储在数据库中，文件系统不可见
- 防止文件名猜测和路径遍历攻击

#### 2. 路径安全（多层防护）

- 所有文件存储在 `/app/data/secure_uploads/` 目录
- 防止目录遍历攻击（../ 路径检测）
- 路径验证确保文件在允许的目录内
- 绝对路径验证，防止符号链接攻击

#### 3. 访问控制（企业级验证）

- JWT Token 验证用户身份（第一层验证）
- 数据库查询验证文件所有权（第二层验证）
- 文件存在性检查（第三层验证）
- 路径安全性验证（第四层验证）
- 用户数据完全隔离，无法访问他人文件

#### 4. 文件类型限制

```python
ALLOWED_EXTENSIONS = {
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
    'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'},
    'spreadsheets': {'.xls', '.xlsx', '.csv', '.ods'},
    'presentations': {'.ppt', '.pptx', '.odp'},
    'archives': {'.zip', '.rar', '.7z', '.tar', '.gz'}
}
```

#### 5. 文件大小限制

- 最大文件大小：10MB
- 上传前检查文件大小

### 文件存储结构

```
secure_uploads/
├── a1b2c3d4e5f6g7h8.pdf      # 安全文件名
├── b2c3d4e5f6g7h8i9.jpg      # 安全文件名
├── c3d4e5f6g7h8i9j0.docx     # 安全文件名
└── ...
```

### 文件API端点

```
POST /api/files/upload          # 上传文件（需要认证）
GET  /api/files                 # 获取用户文件列表（需要认证）
GET  /api/files/{id}/download   # 下载文件（需要认证+所有权验证）
DELETE /api/files/{id}          # 删除文件（需要认证+所有权验证）
```

## 💰 Budget Planner功能

### Budget Planner概述

Budget Planner是一个智能预算规划工具，允许用户通过自然语言与AI交互来创建、修改和管理个人预算。

### 核心特性

- **自然语言交互**: 用户可以通过聊天方式创建和修改预算
- **智能预算识别**: AI能够识别预算相关的关键词和金额
- **实时预算显示**: 预算数据实时显示在右侧面板
- **会话类型隔离**: Budget Planner会话与普通聊天会话分离
- **权限管理**: 基于会话类型的智能权限控制

### 会话类型系统

#### Main Session (主会话)

- **权限**: 无预算数据访问权限
- **功能**: 提供一般性财务建议
- **界面**: 标准两栏布局

#### Budget Planner Session (预算规划会话)

- **权限**: 完整预算数据访问和修改权限
- **功能**: 预算创建、修改、分析
- **界面**: 三栏布局（侧边栏 + 聊天 + 预算面板）

### 预算数据结构

- **年度预算**: 年度收入和支出计划
- **月度预算**: 月度收入和支出计划
- **预算项目**: 具体的收入和支出项目
- **储蓄目标**: 自动计算的储蓄目标

### 智能预算识别

AI能够识别以下类型的预算信息：

- **收入类**: 工资、收入、投资回报等
- **支出类**: 房贷、房租、食物、交通、娱乐等
- **预算设置**: 总预算、年度预算、月度预算等

### 预算操作示例

```
用户: "我的月收入是5000美元，房贷2000美元"
AI: 成功创建月度预算，收入$5000，房贷$2000

用户: "把房贷改为2500美元"
AI: 已更新房贷金额为$2500

用户: "显示我的预算情况"
AI: 显示完整的预算概览和分析
```

## 🧠 智能上下文管理

### 上下文架构

```
用户发送消息 → Backend查询历史 → 构建上下文 → 发送给Brain → 保存新消息
     ↓              ↓              ↓           ↓           ↓
  当前消息    数据库查询    智能上下文构建   AI处理    数据库存储
```

### 上下文构建策略

1. **系统提示**: 明确AI的角色和响应指导
2. **对话摘要**: 历史话题的智能摘要（超过5条消息时）
3. **最近对话**: 最近5条详细对话记录
4. **当前问题**: 明确标识当前需要回答的问题

### 消息结构

```json
{
  "role": "user",
  "content": "用户消息内容",
  "context_type": "current",  // 标识消息类型
  "is_current": true,         // 是否为当前问题
  "timestamp": "2025-10-21T23:45:00"
}
```

### 上下文长度控制

- **最大长度**: 10条消息（可配置）
- **摘要机制**: 超过5条消息时自动生成摘要
- **质量优化**: 过滤重要消息，提高上下文质量
- **性能优化**: 避免token超限，保持响应速度

### AI响应指导

系统提示明确告诉AI：

1. 只回答"current"消息
2. 使用"history"消息作为上下文
3. 不要重复回答历史问题
4. 保持对话连续性

## 🚀 部署配置

### Docker配置

#### 开发环境 (`docker-compose.dev.yml`)

```yaml
services:
  brain:
    build: ./brain
    ports: ["8001:8001"]
    volumes:
      - ./brain:/app
      - ./.env:/app/.env
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=sqlite:///./data/financial_advisor.db
    volumes:
      - ./backend:/app
      - ./web:/app/web
      - ./.env:/app/.env
      - ./backend_data:/app/data
      - ./secure_uploads:/app/data/secure_uploads
    depends_on: [brain]
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### 生产环境 (`docker-compose.yml`)

```yaml
services:
  brain:
    build: ./brain
    ports: ["8001:8001"]
    volumes:
      - ./.env:/app/.env:ro
    restart: unless-stopped

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=sqlite:///./data/financial_advisor.db
    volumes:
      - ./web:/app/web:ro
      - ./.env:/app/.env:ro
      - ./backend_data:/app/data
      - ./secure_uploads:/app/data/secure_uploads
    depends_on: [brain]
    restart: unless-stopped
```

### 环境变量配置 (`.env`)

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=2000

# 服务配置
BACKEND_PORT=8000
BRAIN_SERVICE_URL=http://brain:8001
DEBUG=true
```

## 📂 项目文件结构

```
FINANCIAL_ADVISOR/
├── backend/                    # 后端服务
│   ├── models.py              # 数据库模型
│   ├── database.py            # 数据库配置
│   ├── auth.py                # 认证工具
│   ├── file_storage.py        # 文件存储工具
│   ├── security.py            # 安全工具
│   ├── main.py                # FastAPI应用
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile             # Docker配置
├── brain/                     # AI服务
│   ├── ai_service.py          # AI服务逻辑
│   ├── main.py                # FastAPI应用
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile             # Docker配置
├── web/                       # 前端
│   └── index.html             # 主页面
├── backend_data/              # 数据库文件
│   └── financial_advisor.db   # SQLite数据库
├── secure_uploads/            # 安全文件存储
├── docker-compose.yml         # 生产环境配置
├── docker-compose.dev.yml     # 开发环境配置
├── .env                       # 环境变量
└── SIMPLE_README.md           # 本文档
```

## 🛠️ 开发指南

### 启动开发环境

```bash
# 启动开发服务（热重载）
python dev_start.py

# 或直接使用docker-compose
docker-compose -f docker-compose.dev.yml up --build -d
```

### 启动生产环境

```bash
# 启动生产服务
python start_docker.py

# 或直接使用docker-compose
docker-compose up --build -d
```

### 服务访问

- **前端界面**: http://localhost:8000
- **后端API**: http://localhost:8000/api/
- **Brain服务**: http://localhost:8001
- **API文档**: http://localhost:8000/docs

### 管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

## 🔒 安全考虑

### 已实现的安全措施（企业级标准）

1. **密码安全**: bcrypt加密存储，salt值随机生成，防止彩虹表攻击
2. **JWT认证**: 30分钟自动过期，签名验证，防止Token伪造
3. **文件安全**: SHA256哈希文件名，多层路径验证，防止文件泄露
4. **访问控制**: 四层验证机制，用户数据完全隔离
5. **文件类型限制**: 白名单机制，只允许安全文件类型
6. **文件大小限制**: 最大10MB，防止存储攻击
7. **路径遍历防护**: 绝对路径验证，防止目录遍历攻击
8. **数据加密**: 敏感数据全程加密传输和存储
9. **会话管理**: 自动过期机制，防止会话劫持
10. **输入验证**: 所有用户输入严格验证和过滤

### 生产环境建议

1. **HTTPS**: 使用SSL证书
2. **防火墙**: 限制端口访问
3. **备份**: 定期备份数据库和文件
4. **监控**: 添加日志监控和告警
5. **更新**: 定期更新依赖包

## 📝 API文档

### 认证相关

- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息

### 聊天相关

- `POST /api/chat` - 发送消息
- `GET /api/chat/sessions` - 获取聊天会话列表
- `GET /api/chat/sessions/{id}/messages` - 获取会话消息

### 文件相关

- `POST /api/files/upload` - 上传文件
- `GET /api/files` - 获取文件列表
- `GET /api/files/{id}/download` - 下载文件
- `DELETE /api/files/{id}` - 删除文件

### 系统相关

- `GET /health` - 健康检查
- `GET /` - 前端页面

## 🎯 功能特性

### 已实现功能

- ✅ 用户注册/登录（邀请码：JEFF）
- ✅ JWT认证和会话管理（企业级安全）
- ✅ AI聊天对话（DeepSeek API）
- ✅ 智能上下文管理（最大10条消息）
- ✅ 对话摘要功能（自动生成历史摘要）
- ✅ 聊天历史管理（数据隔离）
- ✅ 文件上传/下载（加密存储）
- ✅ 安全文件存储（SHA256哈希）
- ✅ 响应式前端界面
- ✅ 侧边栏导航和滚动功能
- ✅ Markdown消息渲染
- ✅ 多层访问控制验证
- ✅ 密码bcrypt加密存储
- ✅ 上下文状态显示
- ✅ Budget Planner智能预算规划
- ✅ 基于会话类型的权限管理
- ✅ 用户资料库管理
- ✅ 预算数据持久化存储
- ✅ 智能预算识别和修改
- ✅ 动态界面布局切换
- ✅ 预算历史会话管理

### 技术特点

- 🚀 轻量级架构
- 🧠 智能上下文管理（LangGraph + DeepSeek）
- 🔒 企业级安全加密（bcrypt + JWT + SHA256）
- 📱 响应式设计
- 🔄 热重载开发
- 🐳 Docker容器化
- 📊 SQLite数据库
- 🎨 现代UI设计
- 🛡️ 四层安全验证机制
- 🔐 数据完全隔离保护
- ⚡ 高性能AI响应
- 🎯 智能对话摘要
- 💰 智能预算规划（AI驱动）
- 🔐 基于会话类型的权限管理
- 📊 实时预算数据管理
- 🎛️ 动态界面布局切换
- 🧩 模块化架构设计

## 📚 模块文档

### 核心模块

- [Backend API模块](backend/README.md) - 后端API服务和数据库管理
- [Brain AI模块](brain/README.md) - AI智能服务和上下文管理
- [Web前端模块](web/README.md) - 用户界面和交互功能
- [Docker配置模块](docker/README.md) - 容器化部署配置

### 技术文档

- [API文档](http://localhost:8000/docs) (启动服务后访问)
- [项目架构图](docs/architecture.md)
- [部署指南](docs/deployment.md)

## 📞 支持

如有问题或建议，请查看：

1. 检查Docker服务状态
2. 查看服务日志
3. 验证环境变量配置
4. 确认API密钥设置
5. 参考各模块的详细文档

---

**版本**: 1.0.0
**最后更新**: 2025-10-21
**架构**: 微服务 + 安全文件存储
#   f i n a n c i a l _ a d v i s o r  
 