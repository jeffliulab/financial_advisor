import requests

# # 打开工具（三栏布局）
# requests.post('http://localhost:8000/api/ui/command', json={
#     "command": "open_dashboard",
#     "params": {"tool": "budget-planner"}
# })

# 关闭工具（恢复二栏）
requests.post('http://localhost:8000/api/ui/command', json={
    "command": "close_dashboard",
    "params": {}
})
