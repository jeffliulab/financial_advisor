"""
═══════════════════════════════════════════════════════════════════════════
chat_history.py - 聊天历史管理模块
═══════════════════════════════════════════════════════════════════════════

【输入】
  - username: str              (用户名)
  - session_id: str            (会话ID，UUID格式)
  - role: str                  (消息角色: 'user' 或 'assistant')
  - content: str               (消息内容)
  - limit: int                 (消息数量限制)

【处理】
  - 创建/加载会话
  - 添加消息到会话
  - 更新会话索引
  - 查询会话列表
  - 构建对话上下文
  - 会话标题生成

【输出】
  - create_session() → dict          (新会话信息)
  - add_message() → dict             (新消息信息)
  - get_messages() → list[dict]      (消息列表)
  - get_all_sessions() → list[dict]  (会话列表)
  - build_conversation_context() → list[dict]  (AI上下文)

【数据文件】
  - data/users/{username}/sessions/index.json          (会话索引)
  - data/users/{username}/sessions/{session_id}.json   (会话消息)

【数据格式】
  会话: {id, title, created_at, updated_at, message_count, messages[]}
  消息: {id, role, content, created_at, session_id}
═══════════════════════════════════════════════════════════════════════════
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict


# ============================================================================
#                               路径管理
# ============================================================================

def get_user_sessions_dir(username: str) -> Path:
    """
    获取用户会话目录
    
    Args:
        username: 用户名
        
    Returns:
        Path: 会话目录路径
    """
    sessions_dir = Path("data/users") / username / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_index_path(username: str) -> Path:
    """
    获取会话索引文件路径
    
    Args:
        username: 用户名
        
    Returns:
        Path: 索引文件路径
    """
    return get_user_sessions_dir(username) / "index.json"


def get_session_file_path(username: str, session_id: str) -> Path:
    """
    获取会话文件路径
    
    Args:
        username: 用户名
        session_id: 会话ID
        
    Returns:
        Path: 会话文件路径
    """
    return get_user_sessions_dir(username) / f"{session_id}.json"


# ============================================================================
#                               会话索引管理
# ============================================================================

def load_session_index(username: str) -> dict:
    """
    加载会话索引
    
    Args:
        username: 用户名
        
    Returns:
        dict: 会话索引数据
    """
    index_file = get_session_index_path(username)
    
    if not index_file.exists():
        # 创建空索引
        index_data = {"sessions": []}
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        return index_data
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading session index for {username}: {e}")
        return {"sessions": []}


def save_session_index(username: str, index_data: dict) -> bool:
    """
    保存会话索引
    
    Args:
        username: 用户名
        index_data: 索引数据
        
    Returns:
        bool: 保存是否成功
    """
    index_file = get_session_index_path(username)
    
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving session index for {username}: {e}")
        return False


# ============================================================================
#                               会话管理
# ============================================================================

def create_session(username: str, first_message: str = None) -> dict:
    """
    创建新会话
    
    Args:
        username: 用户名
        first_message: 首条消息（用于生成标题）
        
    Returns:
        dict: 会话信息
    """
    # 生成会话ID
    session_id = str(uuid.uuid4())
    
    # 生成会话标题（从首条消息提取，最多30个字符）
    if first_message:
        title = first_message[:30] + ("..." if len(first_message) > 30 else "")
    else:
        title = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # 创建会话数据
    session_data = {
        "id": session_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "message_count": 0,
        "messages": []
    }
    
    # 保存会话文件
    session_file = get_session_file_path(username, session_id)
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    # 更新会话索引
    index_data = load_session_index(username)
    index_data["sessions"].insert(0, {
        "id": session_id,
        "title": title,
        "created_at": session_data["created_at"],
        "updated_at": session_data["updated_at"],
        "message_count": 0
    })
    save_session_index(username, index_data)
    
    return {
        "id": session_id,
        "title": title,
        "created_at": session_data["created_at"],
        "updated_at": session_data["updated_at"],
        "message_count": 0
    }


def load_session(username: str, session_id: str) -> Optional[dict]:
    """
    加载会话数据
    
    Args:
        username: 用户名
        session_id: 会话ID
        
    Returns:
        dict: 会话数据，如果不存在返回None
    """
    session_file = get_session_file_path(username, session_id)
    
    if not session_file.exists():
        return None
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading session {session_id} for {username}: {e}")
        return None


def save_session(username: str, session_id: str, session_data: dict) -> bool:
    """
    保存会话数据
    
    Args:
        username: 用户名
        session_id: 会话ID
        session_data: 会话数据
        
    Returns:
        bool: 保存是否成功
    """
    session_file = get_session_file_path(username, session_id)
    
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引中的时间戳
        index_data = load_session_index(username)
        for session_info in index_data["sessions"]:
            if session_info["id"] == session_id:
                session_info["updated_at"] = session_data["updated_at"]
                session_info["message_count"] = session_data["message_count"]
                break
        save_session_index(username, index_data)
        
        return True
    except Exception as e:
        print(f"Error saving session {session_id} for {username}: {e}")
        return False


# ============================================================================
#                               消息管理
# ============================================================================

def add_message(username: str, session_id: str, role: str, content: str) -> Optional[dict]:
    """
    添加消息到会话
    
    Args:
        username: 用户名
        session_id: 会话ID
        role: 消息角色（'user' 或 'assistant'）
        content: 消息内容
        
    Returns:
        dict: 消息信息，如果失败返回None
    """
    # 加载会话
    session_data = load_session(username, session_id)
    if not session_data:
        return None
    
    # 创建消息
    message = {
        "id": len(session_data["messages"]) + 1,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "session_id": session_id
    }
    
    # 添加到会话
    session_data["messages"].append(message)
    session_data["message_count"] = len(session_data["messages"])
    session_data["updated_at"] = message["created_at"]
    
    # 保存会话
    if save_session(username, session_id, session_data):
        return message
    return None


def get_messages(username: str, session_id: str, limit: Optional[int] = None) -> List[dict]:
    """
    获取会话的消息列表
    
    Args:
        username: 用户名
        session_id: 会话ID
        limit: 限制返回的消息数量（从最新开始），None表示全部
        
    Returns:
        list: 消息列表
    """
    session_data = load_session(username, session_id)
    if not session_data:
        return []
    
    messages = session_data.get("messages", [])
    
    if limit and limit > 0:
        # 返回最新的limit条消息
        return messages[-limit:]
    
    return messages


def get_recent_messages(username: str, session_id: str, count: int = 10) -> List[dict]:
    """
    获取最近的消息（用于构建上下文）
    
    Args:
        username: 用户名
        session_id: 会话ID
        count: 消息数量
        
    Returns:
        list: 消息列表
    """
    return get_messages(username, session_id, limit=count)


# ============================================================================
#                               会话查询
# ============================================================================

def get_all_sessions(username: str) -> List[dict]:
    """
    获取用户所有会话列表
    
    Args:
        username: 用户名
        
    Returns:
        list: 会话列表（按更新时间倒序）
    """
    index_data = load_session_index(username)
    sessions = index_data.get("sessions", [])
    
    # 按更新时间排序（最新的在前）
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    return sessions


def get_session_info(username: str, session_id: str) -> Optional[dict]:
    """
    获取会话基本信息（不包含消息）
    
    Args:
        username: 用户名
        session_id: 会话ID
        
    Returns:
        dict: 会话信息，如果不存在返回None
    """
    index_data = load_session_index(username)
    
    for session in index_data.get("sessions", []):
        if session["id"] == session_id:
            return session
    
    return None


def session_exists(username: str, session_id: str) -> bool:
    """
    检查会话是否存在
    
    Args:
        username: 用户名
        session_id: 会话ID
        
    Returns:
        bool: 会话是否存在
    """
    return get_session_file_path(username, session_id).exists()


# ============================================================================
#                               会话操作
# ============================================================================

def delete_session(username: str, session_id: str) -> bool:
    """
    删除会话
    
    Args:
        username: 用户名
        session_id: 会话ID
        
    Returns:
        bool: 删除是否成功
    """
    # 删除会话文件
    session_file = get_session_file_path(username, session_id)
    if session_file.exists():
        try:
            session_file.unlink()
        except Exception as e:
            print(f"Error deleting session file: {e}")
            return False
    
    # 从索引中移除
    index_data = load_session_index(username)
    index_data["sessions"] = [
        s for s in index_data["sessions"] if s["id"] != session_id
    ]
    return save_session_index(username, index_data)


def update_session_title(username: str, session_id: str, new_title: str) -> bool:
    """
    更新会话标题
    
    Args:
        username: 用户名
        session_id: 会话ID
        new_title: 新标题
        
    Returns:
        bool: 更新是否成功
    """
    # 更新会话文件
    session_data = load_session(username, session_id)
    if not session_data:
        return False
    
    session_data["title"] = new_title
    session_data["updated_at"] = datetime.utcnow().isoformat()
    
    if not save_session(username, session_id, session_data):
        return False
    
    # 更新索引
    index_data = load_session_index(username)
    for session in index_data["sessions"]:
        if session["id"] == session_id:
            session["title"] = new_title
            session["updated_at"] = session_data["updated_at"]
            break
    
    return save_session_index(username, index_data)


# ============================================================================
#                               上下文构建
# ============================================================================

def build_conversation_context(username: str, session_id: str, max_messages: int = 10) -> List[dict]:
    """
    构建对话上下文（用于发送给AI）
    
    Args:
        username: 用户名
        session_id: 会话ID
        max_messages: 最大消息数量
        
    Returns:
        list: 上下文消息列表，格式：[{"role": "user/assistant", "content": "..."}]
    """
    messages = get_recent_messages(username, session_id, max_messages)
    
    # 转换为AI API需要的格式
    context = []
    for msg in messages:
        context.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    return context


# ============================================================================
#                               统计功能
# ============================================================================

def get_user_statistics(username: str) -> dict:
    """
    获取用户统计信息
    
    Args:
        username: 用户名
        
    Returns:
        dict: 统计信息
    """
    index_data = load_session_index(username)
    sessions = index_data.get("sessions", [])
    
    total_messages = sum(s.get("message_count", 0) for s in sessions)
    
    return {
        "total_sessions": len(sessions),
        "total_messages": total_messages,
        "latest_session": sessions[0] if sessions else None
    }


# ============================================================================
#                               测试函数
# ============================================================================

if __name__ == "__main__":
    print("=== 测试聊天历史管理模块 ===\n")
    
    test_username = "testuser"
    
    # 创建测试会话
    print("1. 创建新会话...")
    session = create_session(test_username, "你好，我想了解一下投资理财的建议")
    print(f"✓ 会话ID: {session['id']}")
    print(f"  标题: {session['title']}")
    
    session_id = session['id']
    
    # 添加消息
    print("\n2. 添加消息...")
    msg1 = add_message(test_username, session_id, "user", "你好，我想了解一下投资理财的建议")
    msg2 = add_message(test_username, session_id, "assistant", "您好！我很乐意为您提供投资理财建议...")
    msg3 = add_message(test_username, session_id, "user", "我应该如何分配资产？")
    print(f"✓ 已添加 3 条消息")
    
    # 获取消息
    print("\n3. 获取消息...")
    messages = get_messages(test_username, session_id)
    print(f"✓ 共有 {len(messages)} 条消息")
    for msg in messages:
        print(f"  [{msg['role']}]: {msg['content'][:50]}...")
    
    # 获取会话列表
    print("\n4. 获取会话列表...")
    sessions = get_all_sessions(test_username)
    print(f"✓ 共有 {len(sessions)} 个会话")
    for s in sessions:
        print(f"  - {s['title']} ({s['message_count']} 条消息)")
    
    # 获取统计信息
    print("\n5. 获取统计信息...")
    stats = get_user_statistics(test_username)
    print(f"✓ 总会话数: {stats['total_sessions']}")
    print(f"  总消息数: {stats['total_messages']}")

