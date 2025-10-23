# 在本页设计一个LangGraph AI Agent 
# 升级方法：直接替换main.py中的：
# # server/main.py 第305行
# # 旧版本：
# ai_response = chat.generate_response(
#     request.message,
#     context_messages
# )
# # 新版本：
# ai_response = newage.generate_response(
#     request.message,
#     context_messages
# )

"""
接入与返回的格式说明

    # 4. 调用AI生成回复
    ai_response = chat.generate_response(
        request.message,
        context_messages
    )

接入的参数Args:
    user_message: 用户消息
    context_messages: 上下文消息列表（之前的对话）
    include_system_prompt: 是否包含系统提示词（暂时没有用，主要使用上述的两个）

返回的格式说明：
    
    dict: API响应结果
        {
            "success": bool,  # true代表返回成功，false代表返回失败
            "response": str,  # AI的回复内容
            "error": str,     # 错误信息（如果有）
            "usage": dict     # token使用情况
        }
"""