"""
API密钥配置示例文件
复制此文件为 api_keys_local.py 并填入您的真实API密钥

使用方法：
1. 复制此文件: cp api_keys.example.py api_keys_local.py  
2. 编辑 api_keys_local.py，填入您的真实API密钥
3. 确保 api_keys_local.py 在 .gitignore 中，不会被提交

注意：
- 请勿在公共仓库中提交真实的API密钥
- 建议使用环境变量或密钥管理服务管理生产环境的API密钥
- 每个源至少配置一个API密钥才能正常工作
"""

# DeerAPI 密钥池配置
# 注册地址：https://api.deerapi.com/panel
deerapi_pool = {
    "your-email@example.com": [
        {
            "name": "key_1",
            "api_key": "sk-your-deerapi-key-1-here",
        },
        {
            "name": "key_2", 
            "api_key": "sk-your-deerapi-key-2-here",
        },
        # 可以添加更多密钥以提高负载均衡效果
    ]
}

# OpenRouter 密钥池配置
# 注册地址：https://openrouter.ai/settings/keys
openrouter_pool = {
    "your-email@example.com": [
        {
            "name": "key_1",
            "api_key": "sk-or-v1-your-openrouter-key-1-here"
        },
        {
            "name": "key_2",
            "api_key": "sk-or-v1-your-openrouter-key-2-here"
        },
        # 建议配置多个密钥以提高并发处理能力
    ]
}

# DeepInfra 密钥池配置
# 注册地址：https://deepinfra.com/dash/api_keys
deepinfra_pool = {
    "your-email@example.com": [
        {
            "name": "key_1",
            "api_key": "your-deepinfra-key-1-here"
        },
        {
            "name": "key_2",
            "api_key": "your-deepinfra-key-2-here"
        },
        # DeepInfra 密钥通常较短，无特定前缀
    ]
}

# TogetherAI 密钥池配置
# 注册地址：https://api.together.xyz/settings/api-keys
togetherai_pool = {
    "your-email@example.com": [
        {
            "name": "key_1",
            "api_key": "tgp_v1_your-togetherai-key-1-here"
        },
        {
            "name": "key_2",
            "api_key": "tgp_v1_your-togetherai-key-2-here"
        },
        # TogetherAI 密钥以 tgp_v1_ 开头
    ]
}

# Google AI Studio 密钥池配置
# 注册地址：https://aistudio.google.com/app/apikey
google_pool = {
    "your-username": [
        {
            "name": "key_1",
            "api_key": "AIzaSy-your-google-key-1-here"
        },
        {
            "name": "key_2",
            "api_key": "AIzaSy-your-google-key-2-here"
        },
        # Google API 密钥以 AIzaSy 开头
    ]
}

# OpenAI 密钥池配置
# 注册地址：https://platform.openai.com/api-keys
openai_pool = {
    "your-email@example.com": [
        {
            "name": "key_1",
            "api_key": "sk-proj-your-openai-key-1-here"
        },
        {
            "name": "key_2",
            "api_key": "sk-proj-your-openai-key-2-here"
        },
        # OpenAI 项目密钥以 sk-proj- 开头
    ]
}

# Anthropic 密钥池配置
# 注册地址：https://console.anthropic.com/settings/keys
anthropic_pool = {
    "your-username": [
        {
            "name": "key_1",
            "api_key": "sk-ant-api03-your-anthropic-key-1-here"
        },
        {
            "name": "key_2",
            "api_key": "sk-ant-api03-your-anthropic-key-2-here"
        },
        # Anthropic 密钥以 sk-ant-api03- 开头
    ]
}

# 密钥池映射 - 请勿修改此部分
pool_mapping = {
    "deerapi": deerapi_pool,
    "openrouter": openrouter_pool,
    "deepinfra": deepinfra_pool,
    "togetherai": togetherai_pool,
    "google": google_pool,
    "openai": openai_pool,
    "anthropic": anthropic_pool
}

# 配置验证提示
print("API密钥配置示例文件已加载")
print("请复制此文件为 api_keys_local.py 并填入您的真实API密钥")
print("注意：请勿将真实API密钥提交到版本控制系统") 