# Financial Advisor - Simple Architecture

<div align="right">
  <a href="README_CN.md" style="background: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 500;">中文版 / Chinese</a>
</div>

## 📋 Project Overview

This is a simplified financial advisor AI chat system with microservice architecture, featuring **complete user authentication system**, **intelligent context management**, **chat history management**, and **enterprise-grade secure file storage**.

⚠️ **Note**: For production use, private cloud deployment is recommended to ensure user data security.

### 🧠 Core Features

- **Intelligent Context Management**: AI remembers conversation history for coherent intelligent responses
- **User Authentication System**: Complete login/registration with invitation code verification
- **Chat History Management**: Multi-session management with recent chats and full history viewing
- **Secure File Storage**: Enterprise-grade file upload and management functionality
- **Responsive Interface**: Modern chat interface with sidebar and scroll functionality
- **Budget Planner**: Intelligent budget planning tool with budget creation, modification, and analysis
- **Session Type Permissions**: Intelligent permission management system based on session types
- **User Profile Library**: Complete user information management and personalized services

### 🔒 Security Features

- **Password Encryption**: bcrypt algorithm for secure password storage
- **JWT Authentication**: JWT Token for user identity verification with 30-minute auto-expiry
- **File Security**: Enterprise-grade file storage security with filename hashing and path validation
- **Data Isolation**: Complete user data isolation, users can only access their own chat records and files
- **Access Control**: Multi-layer access control verification to prevent unauthorized access

### 🎯 Intelligent Context Features

- **Context Length Control**: Intelligent context management with maximum 10 messages
- **Conversation Summary**: Automatic generation of historical conversation summaries
- **Message Type Recognition**: Intelligent distinction between system prompts, historical conversations, summaries, and current questions
- **AI Response Optimization**: AI provides more intelligent and coherent responses based on context
- **Performance Optimization**: Avoids token limits while maintaining fast response times

## 🏗️ System Architecture

### Overall Architecture Diagram

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

### 🔐 Security Architecture Components

#### Encryption & Authentication Layer

- **bcrypt Password Encryption**: User passwords encrypted with bcrypt algorithm, irreversible encryption
- **JWT Token Authentication**: User identity verification using JWT Token with auto-expiry mechanism
- **File Hash Encryption**: Uploaded filenames encrypted with SHA256 hash, hiding original information
- **Access Control Verification**: Multi-layer verification ensuring users can only access their own data

### Service Components

#### 1. **Web Frontend** (`web/index.html`)

- **Tech Stack**: HTML5 + CSS3 + JavaScript (Vanilla)
- **Features**:
  - User authentication interface (login/registration)
  - Chat interface (with Markdown rendering)
  - Sidebar (chat history, quick actions)
  - Responsive design
- **Port**: 8000 (via Backend service)

#### 2. **Backend API** (`backend/`)

- **Tech Stack**: FastAPI + SQLAlchemy + PyJWT + bcrypt
- **Features**:
  - User authentication and authorization
  - Chat session management
  - File upload/download
  - Database operations
  - Static file serving
- **Port**: 8000

#### 3. **Brain AI Service** (`brain/`)

- **Tech Stack**: FastAPI + LangGraph + DeepSeek API + Permission Management
- **Features**:
  - AI conversation processing (based on session types)
  - LangGraph workflow (intelligent routing)
  - DeepSeek API integration
  - Permission management system
  - User profile library management
  - Budget data management
  - Session type recognition and routing
- **Port**: 8001

## 🗄️ Database Design

### Database Type

- **SQLite** (lightweight, suitable for development and small applications)
- **Location**: `./backend_data/financial_advisor.db`
- **Persistence**: Docker volume mounting

### Data Table Structure

#### Users Table (users)

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    username VARCHAR(50) UNIQUE NOT NULL, -- Username
    password_hash VARCHAR(255) NOT NULL,  -- Password hash
    created_at DATETIME DEFAULT NOW(),    -- Creation time
    updated_at DATETIME DEFAULT NOW()     -- Update time
);
```

#### Chat Sessions Table (chat_sessions)

```sql
CREATE TABLE chat_sessions (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- User ID (foreign key)
    title VARCHAR(200) NOT NULL,          -- Session title
    session_type VARCHAR(20) DEFAULT 'chat', -- Session type ('chat'/'budget')
    created_at DATETIME DEFAULT NOW(),    -- Creation time
    updated_at DATETIME DEFAULT NOW(),    -- Update time
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Chat Messages Table (chat_messages)

```sql
CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    session_id VARCHAR(36) NOT NULL,      -- Session ID (foreign key)
    role VARCHAR(20) NOT NULL,            -- Message role ('user'/'assistant')
    content TEXT NOT NULL,                -- Message content
    created_at DATETIME DEFAULT NOW(),    -- Creation time
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

#### Files Table (files)

```sql
CREATE TABLE files (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- User ID (foreign key)
    session_id VARCHAR(36),               -- Session ID (foreign key, optional)
    filename VARCHAR(255) NOT NULL,       -- Original filename
    secure_filename VARCHAR(255) NOT NULL, -- Secure filename
    file_path VARCHAR(500) NOT NULL,      -- File path
    file_size INTEGER NOT NULL,           -- File size
    file_type VARCHAR(100) NOT NULL,      -- MIME type
    upload_time DATETIME DEFAULT NOW(),   -- Upload time
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

#### Budgets Table (budgets)

```sql
CREATE TABLE budgets (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- User ID (foreign key)
    year INTEGER NOT NULL,                -- Year
    month INTEGER,                        -- Month (NULL for annual budget)
    budget_type VARCHAR(20) NOT NULL,     -- Budget type ('monthly'/'annual')
    total_income DECIMAL(10,2) DEFAULT 0, -- Total income
    total_expenses DECIMAL(10,2) DEFAULT 0, -- Total expenses
    savings_goal DECIMAL(10,2) DEFAULT 0, -- Savings goal
    created_at DATETIME DEFAULT NOW(),    -- Creation time
    updated_at DATETIME DEFAULT NOW(),    -- Update time
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Budget Items Table (budget_items)

```sql
CREATE TABLE budget_items (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    budget_id VARCHAR(36) NOT NULL,       -- Budget ID (foreign key)
    category VARCHAR(100) NOT NULL,       -- Item category
    item_type VARCHAR(20) NOT NULL,       -- Item type ('income'/'expense')
    planned_amount DECIMAL(10,2) NOT NULL, -- Planned amount
    actual_amount DECIMAL(10,2) DEFAULT 0, -- Actual amount
    description TEXT,                     -- Description
    created_at DATETIME DEFAULT NOW(),    -- Creation time
    updated_at DATETIME DEFAULT NOW(),    -- Update time
    FOREIGN KEY (budget_id) REFERENCES budgets(id)
);
```

#### Budget Settings Table (budget_settings)

```sql
CREATE TABLE budget_settings (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- User ID (foreign key)
    show_annual BOOLEAN DEFAULT TRUE,     -- Show annual budget
    show_monthly BOOLEAN DEFAULT TRUE,    -- Show monthly budget
    currency VARCHAR(10) DEFAULT 'USD',   -- Currency type
    created_at DATETIME DEFAULT NOW(),    -- Creation time
    updated_at DATETIME DEFAULT NOW(),    -- Update time
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🔐 User Authentication System

### Authentication Flow

- **JWT Token** authentication (30-minute validity, auto-expiry protection)
- **bcrypt** password encryption storage (irreversible encryption, enterprise-grade security)
- **localStorage** frontend state saving (local storage, supports auto-login)

### 🔒 Encryption Security Mechanism

- **Password Encryption**: bcrypt algorithm with random salt generation, prevents rainbow table attacks
- **Token Security**: JWT signature verification, prevents token forgery and tampering
- **Session Management**: Auto-expiry mechanism, prevents long-term session hijacking
- **Data Isolation**: Complete user data isolation, ensures privacy security

### Registration Flow

```
User Input → Verify Invitation Code("JEFF") → Check Username Uniqueness → Password Encryption → Create User → Generate JWT → Auto Login
```

### Login Flow

```
User Input → Verify Username/Password → Generate JWT → Return User Info → Frontend Save State
```

### API Endpoints

```
POST /api/auth/login      # User login
POST /api/auth/register   # User registration
GET  /api/auth/me         # Get current user info
```

## 📁 Secure File Storage System

### Security Features

#### 1. Filename Security (Enterprise-grade Encryption)

- Uses `SHA256` hash algorithm to generate secure filenames
- Combines timestamp and UUID random numbers to ensure uniqueness
- Original filenames only stored in database, invisible in file system
- Prevents filename guessing and path traversal attacks

#### 2. Path Security (Multi-layer Protection)

- All files stored in `/app/data/secure_uploads/` directory
- Prevents directory traversal attacks (../ path detection)
- Path validation ensures files are within allowed directories
- Absolute path validation, prevents symbolic link attacks

#### 3. Access Control (Enterprise-grade Verification)

- JWT Token verification for user identity (first layer verification)
- Database query verification for file ownership (second layer verification)
- File existence check (third layer verification)
- Path security validation (fourth layer verification)
- Complete user data isolation, users cannot access others' files

#### 4. File Type Restrictions

```python
ALLOWED_EXTENSIONS = {
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
    'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'},
    'spreadsheets': {'.xls', '.xlsx', '.csv', '.ods'},
    'presentations': {'.ppt', '.pptx', '.odp'},
    'archives': {'.zip', '.rar', '.7z', '.tar', '.gz'}
}
```

#### 5. File Size Limitations

- Maximum file size: 10MB
- File size check before upload

### File Storage Structure

```
secure_uploads/
├── a1b2c3d4e5f6g7h8.pdf      # Secure filename
├── b2c3d4e5f6g7h8i9.jpg      # Secure filename
├── c3d4e5f6g7h8i9j0.docx     # Secure filename
└── ...
```

### File API Endpoints

```
POST /api/files/upload          # Upload file (requires authentication)
GET  /api/files                 # Get user file list (requires authentication)
GET  /api/files/{id}/download   # Download file (requires authentication + ownership verification)
DELETE /api/files/{id}          # Delete file (requires authentication + ownership verification)
```

## 💰 Budget Planner Feature

### Budget Planner Overview

Budget Planner is an intelligent budget planning tool that allows users to create, modify, and manage personal budgets through natural language interaction with AI.

### Core Features

- **Natural Language Interaction**: Users can create and modify budgets through chat
- **Intelligent Budget Recognition**: AI can recognize budget-related keywords and amounts
- **Real-time Budget Display**: Budget data displayed in real-time on the right panel
- **Session Type Isolation**: Budget Planner sessions separated from regular chat sessions
- **Permission Management**: Intelligent permission control based on session types

### Session Type System

#### Main Session

- **Permissions**: No budget data access permissions
- **Features**: Provides general financial advice
- **Interface**: Standard two-column layout

#### Budget Planner Session

- **Permissions**: Full budget data access and modification permissions
- **Features**: Budget creation, modification, analysis
- **Interface**: Three-column layout (sidebar + chat + budget panel)

### Budget Data Structure

- **Annual Budget**: Annual income and expense plans
- **Monthly Budget**: Monthly income and expense plans
- **Budget Items**: Specific income and expense items
- **Savings Goals**: Automatically calculated savings goals

### Intelligent Budget Recognition

AI can recognize the following types of budget information:

- **Income**: Salary, income, investment returns, etc.
- **Expenses**: Mortgage, rent, food, transportation, entertainment, etc.
- **Budget Settings**: Total budget, annual budget, monthly budget, etc.

### Budget Operation Examples

```
User: "My monthly income is $5000, mortgage is $2000"
AI: Successfully created monthly budget, income $5000, mortgage $2000

User: "Change mortgage to $2500"
AI: Updated mortgage amount to $2500

User: "Show my budget status"
AI: Display complete budget overview and analysis
```

## 🧠 Intelligent Context Management

### Context Architecture

```
User sends message → Backend queries history → Build context → Send to Brain → Save new message
     ↓              ↓              ↓           ↓           ↓
  Current message  Database query  Intelligent context building  AI processing  Database storage
```

### Context Building Strategy

1. **System Prompt**: Clear AI role and response guidance
2. **Conversation Summary**: Intelligent summary of historical topics (when exceeding 5 messages)
3. **Recent Conversations**: Last 5 detailed conversation records
4. **Current Question**: Clearly identify the current question to be answered

### Message Structure

```json
{
  "role": "user",
  "content": "User message content",
  "context_type": "current",  // Message type identifier
  "is_current": true,         // Whether it's the current question
  "timestamp": "2025-10-21T23:45:00"
}
```

### Context Length Control

- **Maximum Length**: 10 messages (configurable)
- **Summary Mechanism**: Auto-generate summary when exceeding 5 messages
- **Quality Optimization**: Filter important messages, improve context quality
- **Performance Optimization**: Avoid token limits, maintain response speed

### AI Response Guidance

System prompts clearly tell AI:

1. Only answer "current" messages
2. Use "history" messages as context
3. Don't repeat answers to historical questions
4. Maintain conversation continuity

## 🚀 Deployment Configuration

### Docker Configuration

#### Development Environment (`docker-compose.dev.yml`)

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

#### Production Environment (`docker-compose.yml`)

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

### Environment Variables Configuration (`.env`)

```env
# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=2000

# Service Configuration
BACKEND_PORT=8000
BRAIN_SERVICE_URL=http://brain:8001
DEBUG=true
```

## 📂 Project File Structure

```
FINANCIAL_ADVISOR/
├── backend/                    # Backend service
│   ├── models.py              # Database models
│   ├── database.py            # Database configuration
│   ├── auth.py                # Authentication utilities
│   ├── file_storage.py        # File storage utilities
│   ├── security.py            # Security utilities
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Docker configuration
├── brain/                     # AI service
│   ├── ai_service.py          # AI service logic
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Docker configuration
├── web/                       # Frontend
│   └── index.html             # Main page
├── backend_data/              # Database files
│   └── financial_advisor.db   # SQLite database
├── secure_uploads/            # Secure file storage
├── docker-compose.yml         # Production environment configuration
├── docker-compose.dev.yml     # Development environment configuration
├── .env                       # Environment variables
└── README.md                  # This document
```

## 🛠️ Development Guide

### Start Development Environment

```bash
# Start development services (hot reload)
python dev_start.py

# Or use docker-compose directly
docker-compose -f docker-compose.dev.yml up --build -d
```

### Start Production Environment

```bash
# Start production services
python start_docker.py

# Or use docker-compose directly
docker-compose up --build -d
```

### Service Access

- **Frontend Interface**: http://localhost:8000
- **Backend API**: http://localhost:8000/api/
- **Brain Service**: http://localhost:8001
- **API Documentation**: http://localhost:8000/docs

### Management Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

## 🔒 Security Considerations

### Implemented Security Measures (Enterprise-grade Standards)

1. **Password Security**: bcrypt encryption storage, random salt generation, prevents rainbow table attacks
2. **JWT Authentication**: 30-minute auto-expiry, signature verification, prevents token forgery
3. **File Security**: SHA256 hash filenames, multi-layer path validation, prevents file leaks
4. **Access Control**: Four-layer verification mechanism, complete user data isolation
5. **File Type Restrictions**: Whitelist mechanism, only allows safe file types
6. **File Size Limitations**: Maximum 10MB, prevents storage attacks
7. **Path Traversal Protection**: Absolute path validation, prevents directory traversal attacks
8. **Data Encryption**: Sensitive data encrypted throughout transmission and storage
9. **Session Management**: Auto-expiry mechanism, prevents session hijacking
10. **Input Validation**: Strict validation and filtering of all user inputs

### Production Environment Recommendations

1. **HTTPS**: Use SSL certificates
2. **Firewall**: Restrict port access
3. **Backup**: Regular database and file backups
4. **Monitoring**: Add log monitoring and alerts
5. **Updates**: Regular dependency package updates

## 📝 API Documentation

### Authentication Related

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user info

### Chat Related

- `POST /api/chat` - Send message
- `GET /api/chat/sessions` - Get chat session list
- `GET /api/chat/sessions/{id}/messages` - Get session messages

### File Related

- `POST /api/files/upload` - Upload file
- `GET /api/files` - Get file list
- `GET /api/files/{id}/download` - Download file
- `DELETE /api/files/{id}` - Delete file

### System Related

- `GET /health` - Health check
- `GET /` - Frontend page

## 🎯 Feature List

### Implemented Features

- ✅ User registration/login (invitation code: JEFF)
- ✅ JWT authentication and session management (enterprise-grade security)
- ✅ AI chat conversation (DeepSeek API)
- ✅ Intelligent context management (maximum 10 messages)
- ✅ Conversation summary functionality (automatic historical summary generation)
- ✅ Chat history management (data isolation)
- ✅ File upload/download (encrypted storage)
- ✅ Secure file storage (SHA256 hash)
- ✅ Responsive frontend interface
- ✅ Sidebar navigation and scroll functionality
- ✅ Markdown message rendering
- ✅ Multi-layer access control verification
- ✅ Password bcrypt encryption storage
- ✅ Context status display
- ✅ Budget Planner intelligent budget planning
- ✅ Permission management based on session types
- ✅ User profile library management
- ✅ Budget data persistent storage
- ✅ Intelligent budget recognition and modification
- ✅ Dynamic interface layout switching
- ✅ Budget history session management

### Technical Features

- 🚀 Lightweight architecture
- 🧠 Intelligent context management (LangGraph + DeepSeek)
- 🔒 Enterprise-grade security encryption (bcrypt + JWT + SHA256)
- 📱 Responsive design
- 🔄 Hot reload development
- 🐳 Docker containerization
- 📊 SQLite database
- 🎨 Modern UI design
- 🛡️ Four-layer security verification mechanism
- 🔐 Complete data isolation protection
- ⚡ High-performance AI response
- 🎯 Intelligent conversation summary
- 💰 Intelligent budget planning (AI-driven)
- 🔐 Permission management based on session types
- 📊 Real-time budget data management
- 🎛️ Dynamic interface layout switching
- 🧩 Modular architecture design

## 📚 Module Documentation

### Core Modules

- [Backend API Module](backend/README.md) - Backend API service and database management
- [Brain AI Module](brain/README.md) - AI intelligent service and context management
- [Web Frontend Module](web/README.md) - User interface and interaction features
- [Docker Configuration Module](docker/README.md) - Containerized deployment configuration

### Technical Documentation

- [API Documentation](http://localhost:8000/docs) (access after starting services)
- [Project Architecture Diagram](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)

## 📞 Support

For questions or suggestions, please check:

1. Check Docker service status
2. View service logs
3. Verify environment variable configuration
4. Confirm API key settings
5. Refer to detailed documentation of each module

---

**Version**: 1.0.0
**Last Updated**: 2025-10-21
**Architecture**: Microservices + Secure File Storage