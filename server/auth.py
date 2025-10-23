"""
═══════════════════════════════════════════════════════════════════════════
auth.py - 用户认证模块
═══════════════════════════════════════════════════════════════════════════

【输入】
  - username: str          (用户名)
  - password: str          (明文密码)
  - token: str            (JWT Token)

【处理】
  - 密码加密验证 (bcrypt)
  - JWT Token生成/验证
  - 用户数据读写 (JSON文件)
  - Token过期检查

【输出】
  - authenticate_user()   → dict | None  (用户信息或None)
  - create_access_token() → str          (JWT Token)
  - get_current_user()    → dict | None  (当前用户信息)
  - verify_password()     → bool         (密码是否正确)

【依赖】
  - passlib (密码加密)
  - python-jose (JWT处理)
  
【数据文件】
  - data/users/{username}.json  (用户信息存储)
═══════════════════════════════════════════════════════════════════════════
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

import bcrypt
from jose import JWTError, jwt

# ============================================================================
#                               配置常量
# ============================================================================

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-please-use-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 用户数据目录
DATA_DIR = Path("data/users")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
#                               密码处理函数
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    加密密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: 加密后的密码
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


# ============================================================================
#                               用户数据管理
# ============================================================================

def get_user_file_path(username: str) -> Path:
    """
    获取用户数据文件路径
    
    Args:
        username: 用户名
        
    Returns:
        Path: 用户数据文件路径
    """
    return DATA_DIR / f"{username}.json"


def load_user_data(username: str) -> Optional[dict]:
    """
    加载用户数据
    
    Args:
        username: 用户名
        
    Returns:
        dict: 用户数据，如果用户不存在返回None
    """
    user_file = get_user_file_path(username)
    
    if not user_file.exists():
        return None
    
    try:
        with open(user_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading user data for {username}: {e}")
        return None


def save_user_data(username: str, user_data: dict) -> bool:
    """
    保存用户数据
    
    Args:
        username: 用户名
        user_data: 用户数据
        
    Returns:
        bool: 保存是否成功
    """
    user_file = get_user_file_path(username)
    
    try:
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving user data for {username}: {e}")
        return False


def user_exists(username: str) -> bool:
    """
    检查用户是否存在
    
    Args:
        username: 用户名
        
    Returns:
        bool: 用户是否存在
    """
    return get_user_file_path(username).exists()


# ============================================================================
#                               JWT Token处理
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    验证并解码token
    
    Args:
        token: JWT token
        
    Returns:
        dict: 解码后的数据，如果token无效返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ============================================================================
#                               认证函数
# ============================================================================

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    验证用户身份
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        dict: 用户信息（不含密码），如果验证失败返回None
    """
    user_data = load_user_data(username)
    
    if not user_data:
        return None
    
    if not verify_password(password, user_data.get("hashed_password", "")):
        return None
    
    # 更新最后登录时间
    user_data["last_login"] = datetime.utcnow().isoformat()
    save_user_data(username, user_data)
    
    # 返回用户信息（不包含密码）
    return {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "created_at": user_data["created_at"],
        "last_login": user_data["last_login"]
    }


def get_current_user(token: str) -> Optional[dict]:
    """
    从token获取当前用户信息
    
    Args:
        token: JWT token
        
    Returns:
        dict: 用户信息，如果token无效返回None
    """
    payload = verify_token(token)
    
    if not payload:
        return None
    
    username = payload.get("sub")
    if not username:
        return None
    
    user_data = load_user_data(username)
    if not user_data:
        return None
    
    return {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "created_at": user_data["created_at"],
        "last_login": user_data.get("last_login")
    }


# ============================================================================
#                               测试函数
# ============================================================================

if __name__ == "__main__":
    # 测试密码加密
    test_password = "test123"
    hashed = get_password_hash(test_password)
    print(f"原始密码: {test_password}")
    print(f"加密密码: {hashed}")
    print(f"验证结果: {verify_password(test_password, hashed)}")
    
    # 测试token生成
    test_data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(test_data)
    print(f"\nToken: {token}")
    
    # 测试token验证
    decoded = verify_token(token)
    print(f"解码结果: {decoded}")

