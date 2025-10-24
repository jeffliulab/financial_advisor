# AI Financial Advisor - API 接口文档

**Frontend Web Application v1.0**

本文档是 AI 财务顾问系统的完整 API 接口说明，包含所有后端接口、调用方式、数据结构和使用示例。

---

## 📚 目录

- [认证相关接口](#认证相关接口)
- [聊天相关接口](#聊天相关接口)
- [UI动态控制接口](#ui动态控制接口)
- [预算规划相关接口](#预算规划相关接口)
- [文件上传接口](#文件上传接口)
- [认证流程说明](#认证流程说明)
- [数据流向图](#数据流向图)
- [开发者注意事项](#开发者注意事项)
- [版本信息](#版本信息)

---

## 认证相关接口

### 1. POST /api/auth/login

**功能**: 用户登录认证

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "username": "用户名 (string, required)",
  "password": "密码 (string, required)"
}
```

**响应成功 200**:
```json
{
  "access_token": "JWT认证令牌 (string)",
  "token_type": "Bearer",
  "user_id": "用户ID (integer)",
  "username": "用户名 (string)"
}
```

**响应失败 401**:
```json
{
  "detail": "Username or Password INCORRECT"
}
```

**调用位置**: `handleLogin()` 函数 - index.html

**说明**: 成功后将token存储到localStorage，用于后续所有需要认证的请求

---

### 2. POST /api/auth/register

**功能**: 用户注册

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "username": "用户名 (string, required)",
  "password": "密码 (string, required)",
  "invite_code": "邀请码 (string, required)"
}
```

**响应成功 200**:
```json
{
  "access_token": "JWT认证令牌 (string)",
  "token_type": "Bearer",
  "user_id": "用户ID (integer)",
  "username": "用户名 (string)"
}
```

**响应失败 400**:
```json
{
  "detail": "错误信息（如：邀请码无效、用户名已存在等）"
}
```

**调用位置**: `handleRegister()` 函数 - index.html

**说明**: 需要有效的邀请码才能注册，成功后自动登录

---

## 聊天相关接口

### 3. POST /api/chat

**功能**: 发送聊天消息，获取AI回复

**请求头**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "message": "用户消息内容 (string, required)",
  "session_id": "会话ID (string, optional) - null表示创建新会话",
  "context_length": "上下文长度 (integer, default: 10) - 最多保留多少条历史消息",
  "include_summary": "是否包含摘要 (boolean, default: true) - 对话摘要优化上下文"
}
```

**响应成功 200**:
```json
{
  "response": "AI回复内容 (string, 支持Markdown格式)",
  "session_id": "会话ID (string) - 用于后续消息关联",
  "message_id": "消息ID (integer)",
  "timestamp": "时间戳 (string, ISO 8601格式)"
}
```

**响应失败 401**:
```json
{
  "detail": "Unauthorized - Token过期或无效"
}
```

**响应失败 500**:
```json
{
  "detail": "Internal Server Error - 服务器错误"
}
```

**调用位置**: `sendMessage()` 函数 - index.html

**说明**:
- 首次发送消息时session_id为null，系统自动创建新会话
- 后续消息使用返回的session_id保持会话连续性
- AI回复支持Markdown格式，前端使用marked.js库渲染
- context_length控制发送给AI的历史消息数量，优化性能和成本

---

### 4. GET /api/chat/sessions

**功能**: 获取当前用户的所有聊天会话列表

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求参数**: 无

**响应成功 200**:
```json
[
  {
    "id": "会话ID (string, UUID)",
    "title": "会话标题 (string) - 通常是第一条消息的摘要",
    "created_at": "创建时间 (string, ISO 8601)",
    "updated_at": "更新时间 (string, ISO 8601)",
    "message_count": "消息数量 (integer)"
  }
]
```

**响应失败 401**:
```json
{
  "detail": "Unauthorized - 需要登录"
}
```

**调用位置**: `loadChatHistory()` 函数 - index.html

**说明**:
- 返回的会话按更新时间倒序排列（最新的在前）
- 前端显示最近3条在侧边栏，点击"History"显示全部
- 用于会话切换和历史记录管理

---

### 5. GET /api/chat/sessions/{session_id}/messages

**功能**: 获取指定会话的所有历史消息

**请求头**:
```
Authorization: Bearer {access_token}
```

**路径参数**:
- `session_id`: 会话ID (string, UUID)

**响应成功 200**:
```json
[
  {
    "id": "消息ID (integer)",
    "role": "消息角色 (string) - 'user' 或 'assistant'",
    "content": "消息内容 (string)",
    "created_at": "创建时间 (string, ISO 8601)",
    "session_id": "所属会话ID (string)"
  }
]
```

**响应失败 401**:
```json
{
  "detail": "Unauthorized - 需要登录"
}
```

**响应失败 404**:
```json
{
  "detail": "Session not found - 会话不存在或无权访问"
}
```

**调用位置**: `loadChatSession()` 函数 - index.html

**说明**:
- 消息按时间顺序返回（旧消息在前，新消息在后）
- 点击侧边栏的历史会话时调用，加载并显示完整对话
- role为'user'的消息显示在右侧，'assistant'的消息显示在左侧

---

## UI动态控制接口

### 6. POST /api/ui/command

**功能**: 发送UI布局切换指令（任何脚本都可调用，无需认证）

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "command": "UI指令类型 (string, required)",
  "params": {
    // 指令参数（根据不同command而不同）
  }
}
```

**可用指令**:

1. **打开Dashboard三栏布局**:
```json
{
  "command": "open_dashboard",
  "params": {
    "tool": "budget-planner | spending-analyzer | investment-dashboard"
  }
}
```

2. **关闭Dashboard恢复二栏**:
```json
{
  "command": "close_dashboard",
  "params": {}
}
```

3. **切换到指定会话**:
```json
{
  "command": "switch_session",
  "params": {
    "session_id": "会话ID"
  }
}
```

**响应成功 200**:
```json
{
  "success": true,
  "message": "Command queued successfully",
  "command_id": "指令ID (string)"
}
```

**响应失败 400**:
```json
{
  "success": false,
  "error": "Invalid command or params"
}
```

**前端轮询**:
- 前端每2秒轮询一次 `GET /api/ui/state` 检查是否有新指令
- 检测到新指令后自动执行并更新UI状态

**调用位置**:
- 前端轮询: `pollUIState()` 函数 (每2秒)
- 指令执行: `executeUICommand()` 函数

**说明**:
- 此接口设计为无认证，任何脚本都可以发送UI控制指令
- Agent/后端可以直接调用此接口控制前端布局
- 前端通过轮询方式自动检测并执行新指令
- 支持指令队列，多个指令按顺序执行

**使用示例**:

Python调用:
```python
import requests

# 打开预算工具
requests.post('http://localhost:8000/api/ui/command', json={
    "command": "open_dashboard",
    "params": {"tool": "budget-planner"}
})

# 关闭Dashboard
requests.post('http://localhost:8000/api/ui/command', json={
    "command": "close_dashboard",
    "params": {}
})
```

JavaScript调用:
```javascript
// 任何脚本都可以直接调用
fetch('/api/ui/command', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        command: 'open_dashboard',
        params: {tool: 'spending-analyzer'}
    })
});
```

---

### 7. GET /api/ui/state

**功能**: 获取当前UI状态和待执行指令（前端轮询使用）

**请求头**: 无（公开端点）

**请求参数**: 无

**响应成功 200**:
```json
{
  "pending_commands": [
    {
      "command": "open_dashboard",
      "params": {"tool": "budget-planner"},
      "timestamp": "2025-10-24T12:00:00Z",
      "command_id": "cmd_123"
    }
  ],
  "current_state": {
    "dashboard_active": false,
    "current_tool": null,
    "layout_mode": "two-column"
  }
}
```

**说明**:
- 前端通过轮询此接口检测新指令
- `pending_commands` 包含所有待执行的指令
- 前端执行完指令后，指令会自动从队列中移除
- 如果没有待执行指令，返回空数组

---

## 预算规划相关接口

### 8. GET /api/budget/dashboard

**功能**: 获取指定年份的Dashboard统计数据

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
- `year`: 年份 (integer, required)

**响应成功 200**:
```json
{
  "year": 2025,
  "total_income": 70000.0,
  "total_expense": 29000.0,
  "total_surplus": 41000.0,
  "monthly_income": 5000.0,
  "monthly_expense": 2000.0,
  "non_monthly_income": 10000.0,
  "non_monthly_expense": 5000.0
}
```

**调用位置**: budget-planner.html

**说明**: 计算指定年份的收入、支出和盈余统计

---

### 9. GET /api/budget/items

**功能**: 获取指定年份和月份的预算项目

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
- `year`: 年份 (integer, required)
- `months`: 月份列表 (string, optional) - 逗号分隔，如 "1,2,3"，"all" 表示所有月份

**响应成功 200**:
```json
{
  "income_items": [
    {
      "id": "item_20251024_123456_0",
      "name": "工资",
      "scope": "永久",
      "time_type": "月度",
      "category": "收入",
      "amount": 5000,
      "created_at": "2025-10-24T12:34:56"
    }
  ],
  "expense_items": [
    {
      "id": "item_20251024_123457_1",
      "name": "房租",
      "scope": "永久",
      "time_type": "月度",
      "category": "支出",
      "amount": 2000,
      "created_at": "2025-10-24T12:34:57"
    }
  ]
}
```

**调用位置**: budget-planner.html

---

### 10. POST /api/budget/items

**功能**: 添加预算项目

**请求头**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "name": "项目名称",
  "scope": "有效范围",  // "永久" 或 "2025年12月" 或 "2025年"
  "time_type": "时间类别",  // "月度" 或 "非月度"
  "category": "收支类别",  // "收入" 或 "支出"
  "amount": 5000
}
```

**响应成功 200**:
```json
{
  "success": true,
  "message": "项目添加成功",
  "item_id": "item_20251024_123456_0"
}
```

---

### 11. DELETE /api/budget/items/{item_id}

**功能**: 删除预算项目

**请求头**:
```
Authorization: Bearer {access_token}
```

**路径参数**:
- `item_id`: 项目ID (string)

**响应成功 200**:
```json
{
  "success": true,
  "message": "项目删除成功"
}
```

---

### 12. GET /api/budget/info

**功能**: 获取用户的预算信息（包含所有项目和可用年份）

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
- `year`: 年份 (integer, optional)

**响应成功 200**:
```json
{
  "items": [...],
  "available_years": [2024, 2025, 2026]
}
```

---

## 文件上传接口

### 13. POST /api/files/upload

**功能**: 上传财务文档（功能预留）

**请求头**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求体**:
```
FormData {
  "file": "文件对象 (File)",
  "file_type": "文件类型 (string) - 如 'bank_statement', 'invoice' 等"
}
```

**响应成功 200**:
```json
{
  "file_id": "文件ID (string)",
  "filename": "文件名 (string)",
  "upload_time": "上传时间 (string)",
  "status": "处理状态 (string)"
}
```

**说明**: 此功能在架构中已设计，需要后端实现

---

## 认证流程说明

### Token管理

```
├─ 存储位置：localStorage.setItem('authToken', token)
├─ 使用方式：所有需要认证的请求都在Header中携带
│             Authorization: Bearer {token}
├─ 过期处理：401响应时自动调用logout()函数
└─ 安全建议：Token应设置合理的过期时间（如24小时）
```

### 会话管理

```
├─ 当前会话：currentSessionId 变量存储
├─ 新建会话：设置 session_id = null 发送消息
├─ 切换会话：点击历史记录加载对应session_id的消息
└─ 会话持久化：所有会话数据存储在后端数据库
```

### 状态持久化

```
├─ localStorage: authToken, currentUser
├─ sessionStorage: 临时会话数据
└─ 内存变量: currentSessionId, messageHistory
```

### 全局认证监控（v1.1 新增）

```
├─ Fetch拦截器：自动检测所有API的401错误
├─ 定期检查：每30秒验证token有效性
├─ 自动弹窗：检测到未登录立即显示登录界面
└─ Token同步：自动将token同步到iframe子页面
```

---

## 数据流向图

### 用户操作流程

```
1. 用户访问
   └─> 检查localStorage中的authToken
       └─> 有效则自动登录

2. 登录/注册
   └─> 获取token
       └─> 存储到localStorage
           └─> 显示聊天界面

3. 发送消息
   └─> POST /api/chat (带token)
       └─> 获取AI回复
           └─> 更新界面

4. 查看历史
   └─> GET /api/chat/sessions
       └─> 显示会话列表

5. 加载会话
   └─> GET /api/chat/sessions/{id}/messages
       └─> 显示历史消息

6. 退出登录
   └─> 清除localStorage
       └─> 刷新页面
           └─> 显示登录界面
```

### 消息上下文优化

```
├─ context_length: 10 (默认保留10条历史消息)
├─ include_summary: true (启用对话摘要)
└─ 作用：减少API调用成本，提高响应速度，保持对话连贯性
```

---

## 开发者注意事项

### 后端实现要求

1. 所有接口必须支持CORS，允许前端跨域访问
2. JWT Token应设置合理的过期时间和刷新机制
3. 用户密码必须加密存储（推荐bcrypt或argon2）
4. 会话数据需要与用户关联，保证数据隔离
5. AI回复支持Markdown格式，建议使用marked.js解析

### 安全建议

1. 实现请求频率限制（Rate Limiting）
2. 验证所有输入数据，防止XSS和SQL注入
3. 敏感操作需要二次验证
4. Token应使用HTTPS传输
5. 定期轮换密钥和更新安全策略

### 性能优化

1. 聊天历史分页加载（当前一次加载全部）
2. 实现WebSocket支持实时消息推送
3. 添加消息缓存机制
4. 对长消息进行分页显示
5. 实现虚拟滚动优化大量消息显示

### API基础URL配置

- **当前配置**: 相对路径 `/api/`
- **生产环境建议**: 配置环境变量 `VITE_API_BASE_URL` 或类似机制
- **示例**: `const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000/api'`

---

## 版本信息

| 项目 | 内容 |
|------|------|
| **前端版本** | v1.1 |
| **创建日期** | 2024 |
| **最后更新** | 2025-10-24 |

### 依赖库

- **marked.js** v9.1.6 (Markdown渲染)
- 无其他外部依赖（使用原生JavaScript）

### 技术栈

- HTML5 + CSS3 + 原生JavaScript (ES6+)
- Fetch API (网络请求)
- LocalStorage (状态持久化)
- 响应式设计 (支持移动端)

### 更新日志

**v1.1 (2025-10-24)**
- ✅ 新增全局认证监控系统
- ✅ 新增Budget Planner完整功能
- ✅ 新增iframe token自动同步
- ✅ 优化UI布局控制系统
- ✅ 所有工具页面文本英文化

**v1.0 (2024)**
- ✅ 基础聊天功能
- ✅ 用户认证系统
- ✅ 会话管理
- ✅ UI动态控制

---

**文件位置**: `web/index接口说明.md`  
**对应前端**: `web/index.html`  
**后端实现**: `server/main.py`


