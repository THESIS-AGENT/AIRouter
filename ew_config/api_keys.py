"""
API密钥配置文件
用于配置各个AI服务提供商的API密钥池

配置格式：
- 第一层：用户标识符（可以是邮箱或用户名）
- 第二层：API密钥列表，每个密钥包含名称和密钥值

请将此文件复制为您的配置文件，并填入真实的API密钥。
建议使用环境变量或密钥管理服务来管理生产环境的API密钥。
"""

# https://api.deerapi.com/panel
# DeerAPI 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "sk-your-deerapi-key-3-here",
        },
        {
            "name": "key_4",
            "api_key": "sk-your-deerapi-key-4-here",
        },
        {
            "name": "key_5",
            "api_key": "sk-your-deerapi-key-5-here",
        }
    ]
}

# https://openrouter.ai/settings/keys
# OpenRouter 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "sk-or-v1-your-openrouter-key-3-here"
        },
        {
            "name": "key_4",
            "api_key": "sk-or-v1-your-openrouter-key-4-here"
        },
        {
            "name": "key_5",
            "api_key": "sk-or-v1-your-openrouter-key-5-here"
        },
    ]
}

# https://deepinfra.com/dash/api_keys
# DeepInfra 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "your-deepinfra-key-3-here"
        },
        {
            "name": "key_4",
            "api_key": "your-deepinfra-key-4-here"
        },
        {
            "name": "key_5",
            "api_key": "your-deepinfra-key-5-here"
        },
    ]
}

# TogetherAI 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "tgp_v1_your-togetherai-key-3-here"
        },
        {
            "name": "key_4",
            "api_key": "tgp_v1_your-togetherai-key-4-here"
        },
        {
            "name": "key_5",
            "api_key": "tgp_v1_your-togetherai-key-5-here"
        },
    ]
}

# https://aistudio.google.com/app/apikey
# Google AI Studio 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "AIzaSy-your-google-key-3-here"
        },
        {
            "name": "key_4",
            "api_key": "AIzaSy-your-google-key-4-here"
        },
        {
            "name": "key_5",
            "api_key": "AIzaSy-your-google-key-5-here"
        },
    ]
}

# https://platform.openai.com/api-keys
# OpenAI 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "sk-proj-your-openai-key-3-here"
        },
        {
            "name": "key_4",
            "api_key": "sk-proj-your-openai-key-4-here"
        },
        {
            "name": "key_5",
            "api_key": "sk-proj-your-openai-key-5-here"
        },
    ]
}

# https://console.anthropic.com/settings/keys
# Anthropic 密钥池配置
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
        {
            "name": "key_3",
            "api_key": "sk-ant-api03-your-anthropic-key-3-here"
        },
        {
            "name": "key_4",
            "api_key": "sk-ant-api03-your-anthropic-key-4-here"
        },
        {
            "name": "key_5",
            "api_key": "sk-ant-api03-your-anthropic-key-5-here"
        },
    ]
}

# 密钥池映射
pool_mapping = {
    "deerapi": deerapi_pool,
    "openrouter": openrouter_pool,
    "deepinfra": deepinfra_pool,
    "togetherai": togetherai_pool,
    "google": google_pool,
    "openai": openai_pool,
    "anthropic": anthropic_pool
}
