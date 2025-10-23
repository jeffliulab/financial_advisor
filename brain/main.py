用langchain实现最基本的聊天功能：

用户发送消息给agent，agent调用LLM，然后LLM返回消息后，agent把消息返回给用户。

调用的LLM是deepseek：

# DeepSeek API Configuration
# 请将下面的YOUR_DEEPSEEK_API_KEY替换为您的实际API密钥

# DeepSeek API Key (必需)
DEEPSEEK_API_KEY=已经保存在环境变量中

# DeepSeek API Base URL (默认值，通常不需要修改)
DEEPSEEK_BASE_URL=https://api.deepseek.com

# DeepSeek Model (默认值，通常不需要修改)
DEEPSEEK_MODEL=deepseek-chat

# API请求参数 (可选，使用默认值即可)
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=2000

# 使用说明：
# 1. 访问 https://platform.deepseek.com/ 获取您的API密钥
# 2. 将 YOUR_DEEPSEEK_API_KEY 替换为您的实际密钥
# 3. 其他参数通常使用默认值即可
