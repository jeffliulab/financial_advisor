"""
═══════════════════════════════════════════════════════════════════════════
register.py - 用户注册模块
═══════════════════════════════════════════════════════════════════════════

【输入】
  - username: str       (用户名，3-30字符)
  - password: str       (密码，至少6字符)
  - invite_code: str    (邀请码)

【处理】
  - 用户名唯一性检查
  - 邀请码验证
  - 密码加密 (bcrypt)
  - 生成用户ID (自增)
  - 创建用户目录结构
  - 初始化用户数据文件

【输出】
  - register_user() → dict
    {
      "success": bool,
      "message": str,
      "user_data": dict,      (如果成功)
      "access_token": str     (如果成功，JWT Token)
    }

【数据文件】
  - data/users/{username}.json          (用户信息)
  - data/users/{username}/sessions/     (会话目录)
  - data/invite_codes.json              (邀请码管理)
  - data/last_user_id.txt               (用户ID计数)

【依赖】
  - auth.py (密码加密、Token生成)
═══════════════════════════════════════════════════════════════════════════
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from auth import (
    get_password_hash,
    user_exists,
    save_user_data,
    create_access_token,
    DATA_DIR
)


# ============================================================================
#                               配置常量
# ============================================================================

# 邀请码配置
INVITE_CODES_FILE = Path("data/invite_codes.json")
DEFAULT_INVITE_CODES = ["JEFF"]


# ============================================================================
#                               邀请码管理
# ============================================================================

def init_invite_codes():
    """
    初始化邀请码文件
    """
    if not INVITE_CODES_FILE.exists():
        INVITE_CODES_FILE.parent.mkdir(parents=True, exist_ok=True)
        invite_data = {
            "active_codes": DEFAULT_INVITE_CODES,
            "used_codes": [],
            "code_history": []
        }
        with open(INVITE_CODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(invite_data, f, ensure_ascii=False, indent=2)


def load_invite_codes() -> dict:
    """
    加载邀请码数据
    
    Returns:
        dict: 邀请码数据
    """
    init_invite_codes()
    
    try:
        with open(INVITE_CODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading invite codes: {e}")
        return {"active_codes": DEFAULT_INVITE_CODES, "used_codes": [], "code_history": []}


def save_invite_codes(invite_data: dict) -> bool:
    """
    保存邀请码数据
    
    Args:
        invite_data: 邀请码数据
        
    Returns:
        bool: 保存是否成功
    """
    try:
        with open(INVITE_CODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(invite_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving invite codes: {e}")
        return False


def validate_invite_code(invite_code: str, mark_as_used: bool = False) -> bool:
    """
    验证邀请码是否有效
    
    Args:
        invite_code: 邀请码
        mark_as_used: 是否标记为已使用（一次性邀请码）
        
    Returns:
        bool: 邀请码是否有效
    """
    invite_data = load_invite_codes()
    
    # 检查是否在激活列表中
    if invite_code not in invite_data.get("active_codes", []):
        return False
    
    # 如果需要标记为已使用（一次性邀请码功能，当前不启用）
    if mark_as_used:
        invite_data["active_codes"].remove(invite_code)
        invite_data["used_codes"].append(invite_code)
        invite_data["code_history"].append({
            "code": invite_code,
            "used_at": datetime.utcnow().isoformat()
        })
        save_invite_codes(invite_data)
    
    return True


# ============================================================================
#                               用户ID生成
# ============================================================================

def get_next_user_id() -> int:
    """
    获取下一个用户ID
    
    Returns:
        int: 新的用户ID
    """
    user_id_file = Path("data/last_user_id.txt")
    
    if not user_id_file.exists():
        user_id_file.parent.mkdir(parents=True, exist_ok=True)
        with open(user_id_file, 'w') as f:
            f.write("0")
        return 1
    
    try:
        with open(user_id_file, 'r') as f:
            last_id = int(f.read().strip())
        
        new_id = last_id + 1
        
        with open(user_id_file, 'w') as f:
            f.write(str(new_id))
        
        return new_id
    except Exception as e:
        print(f"Error getting next user ID: {e}")
        return int(datetime.utcnow().timestamp())


# ============================================================================
#                               用户目录管理
# ============================================================================

def create_user_directories(username: str) -> bool:
    """
    创建用户相关目录
    
    Args:
        username: 用户名
        
    Returns:
        bool: 创建是否成功
    """
    try:
        user_dir = DATA_DIR / username
        sessions_dir = user_dir / "sessions"
        
        user_dir.mkdir(parents=True, exist_ok=True)
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建会话索引文件
        sessions_index = sessions_dir / "index.json"
        if not sessions_index.exists():
            with open(sessions_index, 'w', encoding='utf-8') as f:
                json.dump({"sessions": []}, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Error creating user directories for {username}: {e}")
        return False


# ============================================================================
#                               用户注册
# ============================================================================

def register_user(username: str, password: str, invite_code: str) -> dict:
    """
    注册新用户
    
    Args:
        username: 用户名
        password: 密码
        invite_code: 邀请码
        
    Returns:
        dict: 包含结果的字典
            {
                "success": bool,
                "message": str,
                "user_data": dict (如果成功),
                "access_token": str (如果成功)
            }
    """
    # 1. 验证用户名长度
    if not username or len(username) < 3:
        return {
            "success": False,
            "message": "Username must be at least 3 characters long"
        }
    
    if len(username) > 30:
        return {
            "success": False,
            "message": "Username cannot exceed 30 characters"
        }
    
    # 2. 验证密码强度
    if not password or len(password) < 6:
        return {
            "success": False,
            "message": "Password must be at least 6 characters long"
        }
    
    # 3. 检查用户名是否已存在
    if user_exists(username):
        return {
            "success": False,
            "message": "Username already exists"
        }
    
    # 4. 验证邀请码
    if not validate_invite_code(invite_code):
        return {
            "success": False,
            "message": "Invalid invite code"
        }
    
    # 5. 生成用户ID
    user_id = get_next_user_id()
    
    # 6. 加密密码
    hashed_password = get_password_hash(password)
    
    # 7. 创建用户数据
    user_data = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None,
        "invite_code_used": invite_code,
        "profile": {
            "display_name": username,
            "email": None,
            "avatar": None
        },
        "settings": {
            "theme": "light",
            "language": "zh-CN",
            "notifications": True
        },
        "statistics": {
            "total_sessions": 0,
            "total_messages": 0,
            "total_tokens_used": 0
        }
    }
    
    # 8. 保存用户数据
    if not save_user_data(username, user_data):
        return {
            "success": False,
            "message": "Failed to save user data"
        }
    
    # 9. 创建用户目录
    if not create_user_directories(username):
        return {
            "success": False,
            "message": "Failed to create user directory"
        }
    
    # 10. 生成访问令牌
    access_token = create_access_token(
        data={"sub": username, "user_id": user_id}
    )
    
    # 11. 返回成功结果
    return {
        "success": True,
        "message": "Registration successful",
        "user_data": {
            "user_id": user_id,
            "username": username,
            "created_at": user_data["created_at"]
        },
        "access_token": access_token
    }


# ============================================================================
#                               管理功能
# ============================================================================

def add_invite_code(code: str) -> bool:
    """
    添加新的邀请码
    
    Args:
        code: 邀请码
        
    Returns:
        bool: 添加是否成功
    """
    invite_data = load_invite_codes()
    
    if code in invite_data.get("active_codes", []):
        return False
    
    invite_data["active_codes"].append(code)
    return save_invite_codes(invite_data)


def remove_invite_code(code: str) -> bool:
    """
    移除邀请码
    
    Args:
        code: 邀请码
        
    Returns:
        bool: 移除是否成功
    """
    invite_data = load_invite_codes()
    
    if code not in invite_data.get("active_codes", []):
        return False
    
    invite_data["active_codes"].remove(code)
    return save_invite_codes(invite_data)


def list_active_invite_codes() -> list:
    """
    列出所有有效的邀请码
    
    Returns:
        list: 邀请码列表
    """
    invite_data = load_invite_codes()
    return invite_data.get("active_codes", [])


# ============================================================================
#                               测试函数
# ============================================================================

if __name__ == "__main__":
    print("=== 测试用户注册模块 ===\n")
    
    # 初始化邀请码
    init_invite_codes()
    print(f"有效邀请码: {list_active_invite_codes()}\n")
    
    # 测试注册
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    test_password = "test123456"
    test_invite = "WELCOME2024"
    
    print(f"测试注册用户: {test_username}")
    result = register_user(test_username, test_password, test_invite)
    
    if result["success"]:
        print("✓ 注册成功！")
        print(f"  用户ID: {result['user_data']['user_id']}")
        print(f"  用户名: {result['user_data']['username']}")
        print(f"  Token: {result['access_token'][:50]}...")
    else:
        print(f"✗ 注册失败: {result['message']}")
    
    # 测试重复注册
    print(f"\n测试重复注册同一用户名...")
    result2 = register_user(test_username, test_password, test_invite)
    print(f"结果: {result2['message']}")

