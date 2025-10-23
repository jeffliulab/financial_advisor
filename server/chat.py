"""
═══════════════════════════════════════════════════════════════════════════
chat.py - AI聊天功能模块
═══════════════════════════════════════════════════════════════════════════

【输入】
  - user_message: str              (用户消息)
  - context_messages: list[dict]   (历史对话上下文)
  - model: str                     (AI模型名称，可选)
  - temperature: float             (0.0-2.0，可选)
  - max_tokens: int                (最大token数，可选)

【处理】
  - 构建完整消息列表 (system + context + user)
  - 调用DeepSeek API
  - HTTP请求处理和错误重试
  - 解析AI响应
  - Token使用统计

【输出】
  - generate_response() → dict
    {
      "success": bool,
      "response": str,        (AI回复内容)
      "error": str | None,    (错误信息)
      "usage": dict           (token使用情况)
    }

【环境变量】
  - DEEPSEEK_API_KEY       (必需，API密钥)
  - DEEPSEEK_BASE_URL      (可选，默认: https://api.deepseek.com)
  - DEEPSEEK_MODEL         (可选，默认: deepseek-chat)
  - DEEPSEEK_TEMPERATURE   (可选，默认: 0.7)
  - DEEPSEEK_MAX_TOKENS    (可选，默认: 2000)

【依赖】
  - requests (HTTP客户端)
  - DeepSeek API (兼容OpenAI格式)
═══════════════════════════════════════════════════════════════════════════
"""

import os
import json
from typing import List, Dict, Optional
import requests
from datetime import datetime


# ============================================================================
#                               配置
# ============================================================================

# DeepSeek API 配置（从环境变量读取）
AI_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
AI_API_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
AI_TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))

# 系统提示词
SYSTEM_PROMPT = """You are a professional AI Financial Advisor assistant named Financial Advisor.

Your responsibilities:
1. Provide professional and accurate financial advice and knowledge
2. Help users with budget planning, investment decisions, debt management, etc.
3. Explain complex financial concepts in simple, easy-to-understand language
4. Maintain a friendly, patient, and professional attitude

Important notes:
1. All advice is for reference only and does not constitute specific investment advice
2. Recommend users consult professional advisors before making major financial decisions
3. Protect user privacy, never request or store sensitive financial information
4. If you encounter uncertain questions, be honest about limitations and suggest seeking professional help

Response style:
- Clear and concise, highlighting key points
- Use Markdown format for easy reading
- Use lists, tables, and other structured content when appropriate
- Provide practical advice and action steps
"""


# ============================================================================
#                               AI API 调用
# ============================================================================

def call_ai_api(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> Dict:
    """
    调用DeepSeek API
    该函数的唯一职责是调用DeepSeek API，与 DeepSeek AI 的服务器进行一次完整的网络通信
    并返回API响应结果。
    
    Args:
        messages: 消息列表，格式：[{"role": "user/assistant/system", "content": "..."}]
        model: 模型名称（默认使用环境变量配置）
        temperature: 温度参数（默认使用环境变量配置）
        max_tokens: 最大token数（默认使用环境变量配置）
        stream: 是否使用流式响应
        
    Returns:
        dict: API响应结果
            {
                "success": bool,
                "response": str,  # AI的回复内容
                "error": str,     # 错误信息（如果有）
                "usage": dict     # token使用情况
            }
    """
    if not AI_API_KEY:
        return {
            "success": False,
            "response": "",
            "error": "DeepSeek API key not configured. Please set DEEPSEEK_API_KEY in .env file"
        }
    
    # 使用默认值
    model = model or AI_MODEL
    temperature = temperature if temperature is not None else AI_TEMPERATURE
    max_tokens = max_tokens or AI_MAX_TOKENS
    
    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    # 发送请求
    try:
        api_url = f"{AI_API_BASE_URL.rstrip('/')}/chat/completions"
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 提取回复内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                
                return {
                    "success": True,
                    "response": content,
                    "error": None,
                    "usage": usage
                }
            else:
                return {
                    "success": False,
                    "response": "",
                    "error": "Invalid API response format"
                }
        else:
            error_msg = f"API request failed (status code: {response.status_code})"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"
            
            return {
                "success": False,
                "response": "",
                "error": error_msg
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "response": "",
            "error": "API request timeout. Please try again later"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "response": "",
            "error": "Unable to connect to AI service. Please check your network connection"
        }
    except Exception as e:
        return {
            "success": False,
            "response": "",
            "error": f"调用AI API时发生错误: {str(e)}"
        }


# ============================================================================
#                               对话处理
# ============================================================================

def generate_response(
    user_message: str,
    context_messages: Optional[List[Dict[str, str]]] = None,
    include_system_prompt: bool = True
) -> Dict:
    """
    生成AI回复
    
    Args:
        user_message: 用户消息
        context_messages: 上下文消息列表（之前的对话）
        include_system_prompt: 是否包含系统提示词
        
    Returns:
        dict: 响应结果
            {
                "success": bool,
                "response": str,
                "error": str,
                "usage": dict
            }
    """
    # 构建消息列表
    messages = []
    
    # 添加系统提示词
    if include_system_prompt:
        messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
    
    # 添加上下文消息
    if context_messages:
        messages.extend(context_messages)
    
    # 添加当前用户消息
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # 调用AI API
    return call_ai_api(messages)


def generate_response_with_context(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    max_context_messages: int = 10
) -> Dict:
    """
    带上下文的生成回复（智能截取上下文）
    
    Args:
        user_message: 用户消息
        conversation_history: 完整对话历史
        max_context_messages: 最大上下文消息数量
        
    Returns:
        dict: 响应结果
    """
    # 截取最近的对话作为上下文
    if len(conversation_history) > max_context_messages:
        context = conversation_history[-max_context_messages:]
    else:
        context = conversation_history
    
    return generate_response(user_message, context)


# ============================================================================
#                               会话摘要
# ============================================================================

def generate_conversation_summary(messages: List[Dict[str, str]]) -> str:
    """
    生成对话摘要
    
    Args:
        messages: 消息列表
        
    Returns:
        str: 对话摘要
    """
    if not messages:
        return "新对话"
    
    # 使用第一条用户消息作为摘要
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # 截取前30个字符
            summary = content[:30]
            if len(content) > 30:
                summary += "..."
            return summary
    
    return "新对话"


def generate_ai_summary(messages: List[Dict[str, str]]) -> str:
    """
    使用AI生成对话摘要（可选功能）
    
    Args:
        messages: 消息列表
        
    Returns:
        str: AI生成的摘要
    """
    if not messages or len(messages) < 4:
        return generate_conversation_summary(messages)
    
    # 构建摘要请求
    summary_messages = [
        {
            "role": "system",
            "content": "Summarize the following conversation in one short sentence (max 50 characters):"
        },
        {
            "role": "user",
            "content": "\n".join([f"{m['role']}: {m['content']}" for m in messages[:10]])
        }
    ]
    
    result = call_ai_api(summary_messages, max_tokens=100)
    
    if result["success"]:
        return result["response"][:30]
    else:
        return generate_conversation_summary(messages)


# ============================================================================
#                               测试和诊断
# ============================================================================

def test_ai_connection() -> Dict:
    """
    测试DeepSeek API连接
    
    Returns:
        dict: 测试结果
    """
    test_messages = [
        {"role": "user", "content": "Hello, please reply 'OK' to confirm the connection."}
    ]
    
    result = call_ai_api(test_messages, max_tokens=50)
    
    return {
        "success": result["success"],
        "message": "DeepSeek API connection successful" if result["success"] else f"Connection failed: {result['error']}",
        "response": result.get("response", ""),
        "error": result.get("error")
    }


def get_ai_config() -> Dict:
    """
    获取AI配置信息（用于调试）
    
    Returns:
        dict: 配置信息
    """
    return {
        "api_base_url": AI_API_BASE_URL,
        "model": AI_MODEL,
        "temperature": AI_TEMPERATURE,
        "max_tokens": AI_MAX_TOKENS,
        "api_key_configured": bool(AI_API_KEY),
        "api_key_preview": f"{AI_API_KEY[:10]}..." if AI_API_KEY else "未配置"
    }


# ============================================================================
#                               主函数测试
# ============================================================================

if __name__ == "__main__":
    print("=== 测试聊天功能模块 ===\n")
    
    # 显示配置
    print("1. DeepSeek API配置信息:")
    config = get_ai_config()
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    # 测试连接
    print("\n2. 测试DeepSeek API连接...")
    test_result = test_ai_connection()
    print(f"   结果: {test_result['message']}")
    if test_result['success']:
        print(f"   响应: {test_result['response']}")
    
    # 测试对话
    if test_result['success']:
        print("\n3. 测试对话生成...")
        response = generate_response("Hello, please introduce yourself briefly")
        if response['success']:
            print(f"   ✓ 成功")
            print(f"   回复: {response['response'][:100]}...")
            print(f"   Token使用: {response.get('usage', {})}")
        else:
            print(f"   ✗ 失败: {response['error']}")
    else:
        print("\n⚠️  跳过对话测试（API连接失败）")
        print("\n提示：请确保在.env文件中设置：")
        print("   - DEEPSEEK_API_KEY: 你的DeepSeek API密钥")
        print("   - DEEPSEEK_BASE_URL: API基础URL（可选，默认值通常无需修改）")
        print("   - DEEPSEEK_MODEL: 模型名称（可选，默认值通常无需修改）")
        print("\n获取API密钥: https://platform.deepseek.com/")

