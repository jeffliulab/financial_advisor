"""请不要修改或删除本部分内容
=================================================
项目模块说明与 API 文档
=================================================

-------------------------------------------------
1. LangGraph AI Agent 升级说明
-------------------------------------------------

brain.py编辑好后替换很简单：

在本页设计一个LangGraph AI Agent 
升级方法：直接替换main.py中的：
# server/main.py 第305行
# 旧版本：
ai_response = chat.generate_response(
    request.message,
    context_messages
)
# 新版本：
ai_response = newage.generate_response(
    request.message,
    context_messages
)


-------------------------------------------------
2. AI 接入与返回的格式说明
-------------------------------------------------

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


-------------------------------------------------
3. 页面形态相关 API
-------------------------------------------------

前端页面设置了动态监听接口

获取UI状态：
import requests

# 获取当前UI状态
response = requests.get('http://localhost:8000/api/ui/state')
data = response.json()

print(data['current_state'])
# 输出: {'dashboard_active': True, 'current_tool': 'budget-planner', 'layout_mode': 'three-column'}

控制UI布局：
import requests

# 打开工具（三栏布局）
requests.post('http://localhost:8000/api/ui/command', json={
    "command": "open_dashboard",
    "params": {"tool": "budget-planner"}
})

# 关闭工具（恢复二栏）
requests.post('http://localhost:8000/api/ui/command', json={
    "command": "close_dashboard",
    "params": {}
})

"""




