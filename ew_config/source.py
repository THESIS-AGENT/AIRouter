# 非推理类大语言模型.
# 按照响应时间从快到慢排序
model_list_normal = [
    "gpt41_normal",      # openai|gpt41_normal: 1.87, openrouter|gpt41_normal: 1.65
    "gpt41_mini",        # openai|gpt41_mini: 2.08, openrouter|gpt41_mini: 2.01
    "gemini20_flash",    # google|gemini20_flash: 1.78, deepinfra|gemini20_flash: 2.17, openrouter|gemini20_flash: 2.05
    "llama4_maverick",   # deepinfra|llama4_maverick: 1.65, togetherai|llama4_maverick: 1.89, openrouter|llama4_maverick: 1.97
    "llama4_scout",      # togetherai|llama4_scout: 1.39, openrouter|llama4_scout: 2.28, deepinfra|llama4_scout: 3.01
    "gemini25_flash",    # google|gemini25_flash: 2.17, openrouter|gemini25_flash: 2.17, deepinfra|gemini25_flash: 3.14
    "claude37_normal",   # anthropic|claude37_normal: 2.37, deepinfra|claude37_normal: 2.13, openrouter|claude37_normal: 2.47
    "gemini25_pro",      # google|gemini25_pro: 6.47, deepinfra|gemini25_pro: 3.69, openrouter|gemini25_pro: 7.49
    "gpto4_mini_high",   # openai|gpto4_mini_high: 6.83, openrouter|gpto4_mini_high: 15.22
    "qwen25_72b_instruct", # togetherai|qwen25_72b_instruct: 2.24, deepinfra|qwen25_72b_instruct: 6.29, openrouter|qwen25_72b_instruct: 7.59
    "claude4_opus",      # anthropic|claude4_opus: 3.51, openrouter|claude4_opus: 3.81
    "claude4_sonnet",     # anthropic|claude4_sonnet: 2.84, openrouter|claude4_sonnet: 2.62
    "grok3",
    "grok3_mini",
    "grok4"
]

# 推理类大语言模型.
# 按照响应时间从快到慢排序
model_list_thinking = [
    "gemini25_flash_thinking",  # openrouter|gemini25_flash_thinking: 3.45
    "claude37_thinking",        # openrouter|claude37_thinking: 4.38
    "qwen3_30b_moe",            # 暂无延时数据
    "qwen3_235b_moe",           # togetherai|qwen3_235b_moe: 27.31
    "claude4_opus_thinking",    # 暂无延时数据
    "claude4_sonnet_thinking"   # 暂无延时数据
]

# 非推理类多模态大模型.
# 按照响应时间从快到慢排序
model_list_mm_normal = [
    "gpt41_normal_mm",      # openai|gpt41_normal_mm: 1.36, openrouter|gpt41_normal_mm: 1.35
    "llama4_maverick_mm",   # togetherai|llama4_maverick_mm: 1.05, openrouter|llama4_maverick_mm: 1.40
    "llama4_scout_mm",      # togetherai|llama4_scout_mm: 1.04, openrouter|llama4_scout_mm: 1.20
    "gemini25_flash_mm",    # openrouter|gemini25_flash_mm: 1.69, google|gemini25_flash_mm: 2.96
    "llama32_vl_90b_instruct",  # deepinfra|llama32_vl_90b_instruct: 2.31, togetherai|llama32_vl_90b_instruct: 2.70, openrouter|llama32_vl_90b_instruct: 3.22
    "gemini25_pro_mm",      # google|gemini25_pro_mm: 20.23, openrouter|gemini25_pro_mm: 20.52
    "gpto4_mini_high_mm",   # openai|gpto4_mini_high_mm: 3.23, openrouter|gpto4_mini_high_mm: 7.77
    "qwen25_vl_72b_instruct",  # togetherai|qwen25_vl_72b_instruct: 5.94, openrouter|qwen25_vl_72b_instruct: 11.14
    "claude4_sonnet_mm",     # anthropic|claude4_sonnet_mm: 2.34, openrouter|claude4_sonnet_mm: 2.57
    "grok3_mm",
    "grok4_mm"
]

# 推理类多模态大模型, 例如QvQ-72B, chatGPT o3以及o4-mini
model_list_mm_thinking = []

# PDF文档处理模型列表，只支持Google源的模型
model_list_doc_normal = [
    "gemini20_flash",      # google|gemini20_flash: 支持PDF处理
    "gemini25_flash",      # google|gemini25_flash: 支持PDF处理
    "gemini25_pro",        # google|gemini25_pro: 支持PDF处理
]

model_list_function_calling = ["claude37_normal", "gemini25_pro", "claude4_opus", "claude4_sonnet", "gemini25_flash", "grok4"]

model_list_embedding = ["BAAI/bge-en-icl", "BAAI/bge-large-en-v1.5", "BAAI/bge-m3", "BAAI/bge-m3-multi", "Qwen/Qwen3-Embedding-0.6B", "Qwen/Qwen3-Embedding-4B", "Qwen/Qwen3-Embedding-8B"]
model_list_reranker = ["Qwen/Qwen3-Reranker-0.6B", "Qwen/Qwen3-Reranker-4B", "Qwen/Qwen3-Reranker-8B"]

# 健康检测屏蔽模型清单 - 这些模型仍然可以被LLM_Wrapper使用，但不进行健康检测以避免费用消耗
# 主要用于屏蔽高价模型如claude4_opus等，避免健康检测产生不必要的费用
# 
# 屏蔽逻辑说明：
# 1. 精确屏蔽：如果添加 "model_mm"，只屏蔽多模态版本
# 2. 层级屏蔽：如果添加 "model"，屏蔽该模型的所有版本（包括多模态和非多模态）
health_check_blacklist = [
    # 高价推理模型
    "claude4_opus",           # 非常昂贵的模型（层级屏蔽：同时屏蔽claude4_opus和claude4_opus_mm）
    "claude4_opus_thinking",  # 推理版本更昂贵
    "claude4_sonnet_thinking", # 推理版本相对昂贵
]


def is_model_health_check_blacklisted(model_name):
    """
    检查模型是否在健康检测屏蔽清单中
    
    支持层级屏蔽逻辑：
    1. 精确匹配：如果模型名称直接在屏蔽清单中，则被屏蔽
    2. 层级屏蔽：如果是多模态模型(_mm后缀)，还需检查其基础模型是否被屏蔽
    
    Args:
        model_name (str): 要检查的模型名称
        
    Returns:
        bool: 如果模型应该被屏蔽返回True，否则返回False
        
    Examples:
        # 假设屏蔽清单包含 ["claude4_opus", "gemini25_pro_mm"]
        is_model_health_check_blacklisted("claude4_opus")      # True (精确匹配)
        is_model_health_check_blacklisted("claude4_opus_mm")   # True (层级屏蔽，因为claude4_opus被屏蔽)
        is_model_health_check_blacklisted("gemini25_pro")      # False (基础模型未屏蔽)
        is_model_health_check_blacklisted("gemini25_pro_mm")   # True (精确匹配)
    """
    # 1. 精确匹配检查
    if model_name in health_check_blacklist:
        return True
    
    # 2. 层级屏蔽检查（仅对多模态模型）
    if model_name.endswith("_mm"):
        base_model_name = model_name[:-3]  # 去掉"_mm"后缀
        if base_model_name in health_check_blacklist:
            return True
    
    return False


# 通过source_config可以判断这个源是否支持openai API-SDK调用, 以及CURL调用, 如果不存在相关字段, 则是暂不支持.

source_config = {"openrouter": {"openai": "https://openrouter.ai/api/v1", "curl": "https://openrouter.ai/api/v1/chat/completions"},
                "deepinfra": {"openai": "https://api.deepinfra.com/v1/openai", "curl": "https://api.deepinfra.com/v1/openai/chat/completions"},
                "deerapi": {"openai": "https://api.deerapi.com/v1", "curl": "https://api.deerapi.com/v1/chat/completions"},
                "togetherai": {"openai": "https://api.together.xyz/v1", "curl": "https://api.together.xyz/v1/chat/completions"},
                # 增加了四个官方源.
                "google": {"openai": "https://generativelanguage.googleapis.com/v1beta/openai/", "curl": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"},
                "anthropic": {"openai": "https://api.anthropic.com/v1/", "curl": "https://api.anthropic.com/v1/complete"},
                "openai": {"openai": "https://api.openai.com/v1", "curl": "https://api.openai.com/v1/responses"}
                }

# 该排名用于冷启动时的参考优先级.
source_ranking = {"google": 1, "anthropic": 2, "openai": 3, "openrouter": 4, "deepinfra": 5, "deerapi": 6, "togetherai": 7}

# 逻辑是, 如果一个模型的自定义命名, 以"_mm"结尾, 且value为None, 则查找其同名的非多模态接口.
# 即, 二者为同一个模型接口.
# 如果单纯value为None, 则代表当前源存在该模型.

source_mapping = {
    # https://openrouter.ai/models

    "openrouter": {
        "qwen25_72b_instruct": "qwen/qwen-2.5-72b-instruct",
        "qwen25_vl_72b_instruct": None,
        "llama4_maverick": "meta-llama/llama-4-maverick",
        "llama4_scout": "meta-llama/llama-4-scout",
        "llama32_vl_90b_instruct": None,
        "claude37_normal": "anthropic/claude-3.7-sonnet",
        "claude37_thinking": "anthropic/claude-3.7-sonnet:thinking",
        "gemini20_flash": None,
        "gemini25_flash": "google/gemini-2.5-flash",
        "gemini25_pro": "google/gemini-2.5-pro",
        "gemini25_flash_thinking": "google/gemini-2.5-flash-preview:thinking",
        "gpt41_normal": "openai/gpt-4.1",
        "gpt41_mini": "openai/gpt-4.1-mini",
        "gpto4_mini_high": "openai/o4-mini-high",
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,
        "qwen3_235b_moe": None, 
        "qwen3_30b_moe": None,
        "claude4_opus": "anthropic/claude-opus-4",
        "claude4_sonnet": "anthropic/claude-sonnet-4",
        "claude4_sonnet_thinking": None,
        "claude4_opus_thinking": None,
        "claude4_sonnet_mm": None,
        "grok3": "x-ai/grok-3",
        "grok3_mini": "x-ai/grok-3-mini",
        "grok4": "x-ai/grok-4"
    },
    # https://deepinfra.com/models

    "deepinfra": {
        "qwen25_72b_instruct": "Qwen/Qwen2.5-72B-Instruct",
        "qwen25_vl_72b_instruct": None,
        "llama4_maverick": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "llama4_scout": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "llama32_vl_90b_instruct": "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "claude37_normal": "anthropic/claude-3-7-sonnet-latest",
        "claude37_thinking": None,
        "gemini20_flash": "google/gemini-2.0-flash-001",
        "gemini25_flash": "google/gemini-2.5-flash",
        "gemini25_pro": "google/gemini-2.5-pro",
        "gemini25_flash_thinking": None,
        "gpt41_normal": None,
        "gpt41_mini": None,
        "gpto4_mini_high": None,
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,
        "qwen3_235b_moe": None, 
        "qwen3_30b_moe": None,
        "claude4_opus": None,
        "claude4_sonnet": None,
        "claude4_sonnet_thinking": None,
        "claude4_opus_thinking": None,
        "claude4_sonnet_mm": None,
        "grok3": None,
        "grok3_mini": None,
        "grok4": None
    },
    # https://api.deerapi.com/pricing

    "deerapi": {
        "qwen25_72b_instruct": "Qwen2.5-72B-Instruct-128K",
        "qwen25_vl_72b_instruct": None,
        "llama4_maverick": "llama-4-maverick",
        "llama4_scout": None,  # 移除：测试失败，不可用
        "llama32_vl_90b_instruct": None,
        "claude37_normal": "claude-3-7-sonnet-latest",
        "claude37_thinking": "claude-3-7-sonnet-thinking",
        "gemini20_flash": "gemini-2.0-flash",
        "gemini25_flash": "gemini-2.5-flash",
        "gemini25_pro": "gemini-2.5-pro-preview-06-05",
        "gemini25_flash_thinking": None,
        "gpt41_normal": "gpt-4.1",
        "gpt41_mini": "gpt-4.1-mini",
        "gpto4_mini_high": None,
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,  # 移除：基于llama4_scout，同样不可用
        "qwen3_235b_moe": "qwen3-235b-a22b", 
        "qwen3_30b_moe": "qwen3-30b-a3b",
        "claude4_opus": "claude-opus-4-20250514",
        "claude4_sonnet": "claude-sonnet-4-20250514",
        "claude4_sonnet_thinking": "claude-sonnet-4-20250514-thinking",
        "claude4_opus_thinking": "claude-opus-4-20250514-thinking",
        "claude4_sonnet_mm": None,
        "grok3": "grok-3",
        "grok3_mini": "grok-3-mini",
        "grok4": "grok-4"
    },
    # https://api.together.ai/models

    "togetherai":{
        "qwen25_72b_instruct": "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "qwen25_vl_72b_instruct": "Qwen/Qwen2.5-VL-72B-Instruct",
        "llama4_maverick": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "llama4_scout": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "llama32_vl_90b_instruct": "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
        "claude37_normal": None,
        "claude37_thinking": None,
        "gemini20_flash": None,
        "gemini25_flash": None,
        "gemini25_pro": None,
        "gemini25_flash_thinking": None,
        "gpt41_normal": None,
        "gpt41_mini": None,
        "gpto4_mini_high": None,
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,
        "qwen3_235b_moe": "Qwen/Qwen3-235B-A22B-fp8-tput", 
        "qwen3_30b_moe": None,
        "claude4_opus": None,
        "claude4_sonnet": None,
        "claude4_sonnet_thinking": None,
        "claude4_opus_thinking": None,
        "claude4_sonnet_mm": None,
        "grok3": None,
        "grok3_mini": None,
        "grok4": None
    },
    # https://ai.google.dev/gemini-api/docs/models?hl=zh-cn#gemini-2.5-pro-preview-05-06

    "google":{
        "qwen25_72b_instruct": None,
        "qwen25_vl_72b_instruct": None,
        "llama4_maverick": None,
        "llama4_scout": None,
        "llama32_vl_90b_instruct": None,
        "claude37_normal": None,
        "claude37_thinking": None,
        "gemini20_flash": "gemini-2.0-flash",
        "gemini25_flash": "gemini-2.5-flash",
        "gemini25_pro": "gemini-2.5-pro",
        "gemini25_flash_thinking": None,
        "gpt41_normal": None,
        "gpt41_mini": None,
        "gpto4_mini_high": None,
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,
        "qwen3_235b_moe": None, 
        "qwen3_30b_moe": None,
        "claude4_opus": None,
        "claude4_sonnet": None,
        "claude4_sonnet_thinking": None,
        "claude4_opus_thinking": None,
        "claude4_sonnet_mm": None,
        "grok3": None,
        "grok3_mini": None,
        "grok4": None
    },
    # https://docs.anthropic.com/en/docs/about-claude/models/all-models
    
    "anthropic":{
        "qwen25_72b_instruct": None,
        "qwen25_vl_72b_instruct": None,
        "llama4_maverick": None,
        "llama4_scout": None,
        "llama32_vl_90b_instruct": None,
        "claude37_normal": "claude-3-7-sonnet-latest",
        "claude37_thinking": None,
        "gemini20_flash": None,
        "gemini25_flash": None,
        "gemini25_pro": None,
        "gemini25_flash_thinking": None,
        "gpt41_normal": None,
        "gpt41_mini": None,
        "gpto4_mini_high": None,
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,
        "qwen3_235b_moe": None, 
        "qwen3_30b_moe": None,
        "claude4_opus": "claude-opus-4-20250514",
        "claude4_sonnet": "claude-sonnet-4-20250514",
        "claude4_sonnet_thinking": None,
        "claude4_opus_thinking": None,
        "claude4_sonnet_mm": None,
        "grok3": None,
        "grok3_mini": None,
        "grok4": None
    },
    # https://platform.openai.com/docs/models
    
    "openai":{
        "qwen25_72b_instruct": None,
        "qwen25_vl_72b_instruct": None,
        "llama4_maverick": None,
        "llama4_scout": None,
        "llama32_vl_90b_instruct": None,
        "claude37_normal": None,
        "claude37_thinking": None,
        "gemini20_flash": None,
        "gemini25_flash": None,
        "gemini25_pro": None,
        "gemini25_flash_thinking": None,
        "gpt41_normal": "gpt-4.1-2025-04-14",
        "gpt41_mini": "gpt-4.1-mini-2025-04-14",
        "gpto4_mini_high": "o4-mini-2025-04-16",
        "gemini25_pro_mm": None,
        "gemini25_flash_mm": None,
        "gpt41_normal_mm": None,
        "gpto4_mini_high_mm": None,
        "llama4_maverick_mm": None,
        "llama4_scout_mm": None,
        "qwen3_235b_moe": None, 
        "qwen3_30b_moe": None,
        "claude4_opus": None,
        "claude4_sonnet": None,
        "claude4_sonnet_thinking": None,
        "claude4_opus_thinking": None,
        "claude4_sonnet_mm": None,
        "grok3": None,
        "grok3_mini": None,
        "grok4": None
    },

}

# 输入token价格, 与输出token价格.
# 如果不是tuple, 而是float, 则i/o价格一致.
source_price = {
    # https://openrouter.ai/models
    "openrouter": {
        "qwen/qwen-2.5-72b-instruct": (0.12*1e-6, 0.39*1e-6),
        "meta-llama/llama-4-maverick": (0.17*1e-6, 0.6*1e-6),
        "meta-llama/llama-4-scout": (0.08*1e-6, 0.3*1e-6),
        "anthropic/claude-3.7-sonnet": (3*1e-6, 15*1e-6),
        "anthropic/claude-3.7-sonnet:thinking": (3*1e-6, 15*1e-6),
        "google/gemini-2.5-flash": (0.15*1e-6, 0.6*1e-6),
        "google/gemini-2.5-pro": (1.25*1e-6, 10*1e-6),
        "google/gemini-2.5-flash-preview:thinking": (0.15*1e-6, 3.5*1e-6),
        "openai/gpt-4.1": (2*1e-6, 8*1e-6),
        "openai/gpt-4.1-mini": (0.4*1e-6, 1.6*1e-6),
        "openai/o4-mini-high": (1.1*1e-6, 4.4*1e-6),
        "anthropic/claude-opus-4": (15*1e-6, 75*1e-6),
        "anthropic/claude-sonnet-4": (3*1e-6, 15*1e-6),
        "x-ai/grok-3": (3*1e-6, 15*1e-6),
        "x-ai/grok-3-mini": (0.3*1e-6, 0.5*1e-6),
        "x-ai/grok-4": (3*1e-6, 15*1e-6)
    },
    # https://deepinfra.com/models

    "deepinfra": {
        "Qwen/Qwen2.5-72B-Instruct": (0.12*1e-6, 0.39*1e-6),
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": (0.17*1e-6, 0.6*1e-6),
        "meta-llama/Llama-4-Scout-17B-16E-Instruct": (0.08*1e-6, 0.3*1e-6),
        "meta-llama/Llama-3.2-90B-Vision-Instruct": (0.35*1e-6, 0.4*1e-6),
        "anthropic/claude-3-7-sonnet-latest": (3.3*1e-6, 16.5*1e-6),
        "google/gemini-2.0-flash-001": (0.1*1e-6, 0.4*1e-6),
        "google/gemini-2.5-flash": (0.105*1e-6, 2.45*1e-6),
        "google/gemini-2.5-pro": (0.875*1e-6, 7*1e-6),
    },
    # https://api.deerapi.com/pricing

    "deerapi": {
        "Qwen2.5-72B-Instruct-128K": (4*1e-6, 12*1e-6),
        "llama-4-maverick": (0.6*1e-6, 1.8*1e-6), 
        # "llama-4-scout": (0.27*1e-6, 1.44*1e-6),  # 移除：不可用
        "claude-3-7-sonnet-latest": (3*1e-6, 15*1e-6),
        "claude-3-7-sonnet-thinking": (3*1e-6, 15*1e-6),
        "gemini-2.0-flash": (0.1*1e-6, 0.4*1e-6),
        "gemini-2.5-flash": (0.15*1e-6, 3.5*1e-6),
        "gemini-2.5-pro-preview-06-05": (1.2*1e-6, 10*1e-6),
        "gpt-4.1": (2*1e-6, 8*1e-6),
        "gpt-4.1-mini": (0.4*1e-6, 1.6*1e-6),
        "qwen3-235b-a22b": (0.4*1e-6, 1.2*1e-6),
        "qwen3-30b-a3b": (2*1e-6, 6*1e-6),
        "claude-opus-4-20250514": (15*1e-6, 75*1e-6),
        "claude-sonnet-4-20250514": (3*1e-6, 15*1e-6),
        "claude-sonnet-4-20250514-thinking": (3*1e-6, 15*1e-6),
        "claude-opus-4-20250514-thinking": (15*1e-6, 75*1e-6),
        "grok-3": (3*1e-6, 9*1e-6),
        "grok-3-mini": (0.3*1e-6, 0.9*1e-6),
        "grok-4": (3*1e-6, 9*1e-6)
    },
    # https://api.together.ai/models

    "togetherai":{
        "Qwen/Qwen2.5-72B-Instruct-Turbo": (1.2*1e-6, 1.2*1e-6),
        "Qwen/Qwen2.5-VL-72B-Instruct": (1.98*1e-6, 8*1e-6),
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": (0.27*1e-6, 0.85*1e-6),
        "meta-llama/Llama-4-Scout-17B-16E-Instruct": (0.18*1e-6, 0.59*1e-6),
        "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo": (1.2*1e-6, 1.2*1e-6),
        "Qwen/Qwen3-235B-A22B-fp8-tput": (0.20*1e-6, 0.60*1e-6)
    },
    # https://ai.google.dev/gemini-api/docs/models?hl=zh-cn#gemini-2.5-pro-preview-05-06

    "google":{
        "gemini-2.0-flash": (0.1*1e-6, 0.4*1e-6),
        "gemini-2.5-flash": (0.15*1e-6, 1*1e-6),
        "gemini-2.5-pro": (1.25*1e-6, 10*1e-6),
    },
    # https://docs.anthropic.com/en/docs/about-claude/models/all-models
    
    "anthropic":{
        "claude-3-7-sonnet-latest": (3*1e-6, 15*1e-6),
        "claude-opus-4-20250514":  (15*1e-6, 75*1e-6),
        "claude-sonnet-4-20250514": (3*1e-6, 15*1e-6),
    },
    # https://platform.openai.com/docs/models
    
    "openai":{
        "gpt-4.1-2025-04-14": (2*1e-6, 8*1e-6),
        "gpt-4.1-mini-2025-04-14": (0.4*1e-6, 1.6*1e-6),
        "o4-mini-2025-04-16": (1.1*1e-6, 4.4*1e-6),
    },

}

source_max_ioLength = {
    # https://openrouter.ai/models

    "openrouter": {
        "qwen/qwen-2.5-72b-instruct": 33 * 1e3,
        "meta-llama/llama-4-maverick": 1050 * 1e3,
        "meta-llama/llama-4-scout": 1050 * 1e3,
        "anthropic/claude-3.7-sonnet": 200 * 1e3,
        "anthropic/claude-3.7-sonnet:thinking": 200 * 1e3,
        "google/gemini-2.5-flash": 1050 * 1e3,
        "google/gemini-2.5-pro": 1050 * 1e3,
        "google/gemini-2.5-flash-preview:thinking": 1050 * 1e3,
        "openai/gpt-4.1": 1050 * 1e3,
        "openai/gpt-4.1-mini": 1050 * 1e3,
        "openai/o4-mini-high": 200 * 1e3,
        "anthropic/claude-opus-4": 200*1e3,
        "anthropic/claude-sonnet-4": 200*1e3,
        "x-ai/grok-3": 131072,
        "x-ai/grok-3-mini": 131072,
        "x-ai/grok-4": 256*1e3,
    },
    # https://deepinfra.com/models

    "deepinfra": {
        "Qwen/Qwen2.5-72B-Instruct": 32 * 1e3,
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": 1024 * 1e3,
        "meta-llama/Llama-4-Scout-17B-16E-Instruct": 320 * 1e3,
        "meta-llama/Llama-3.2-90B-Vision-Instruct": 32 * 1e3,
        "anthropic/claude-3-7-sonnet-latest": 195 * 1e3,
        "google/gemini-2.0-flash-001": 976 * 1e3,
        "google/gemini-2.5-flash": 976 * 1e3,
        "google/gemini-2.5-pro": 976 * 1e3,
    },
    # https://api.deerapi.com/pricing

    "deerapi": {
        "Qwen2.5-72B-Instruct-128K": None,
        "llama-4-maverick": None, 
        # "llama-4-scout": None,  # 移除：不可用
        "claude-3-7-sonnet-latest": None,
        "claude-3-7-sonnet-thinking": None,
        "gemini-2.0-flash": None,
        "gemini-2.5-flash": None,
        "gemini-2.5-pro-preview-06-05": None,
        "gpt-4.1": None,
        "gpt-4.1-mini": None,
        "qwen3-235b-a22b": None,
        "qwen3-30b-a3b": None,
        "claude-opus-4-20250514": None,
        "claude-sonnet-4-20250514": None,
        "claude-sonnet-4-20250514-thinking": None,
        "claude-opus-4-20250514-thinking": None,
        "grok-3": 131072,
        "grok-3-mini": 131072,
        "grok-4": 256*1e3,
    },
    # https://api.together.ai/models

    "togetherai":{
        "Qwen/Qwen2.5-72B-Instruct-Turbo": None,
        "Qwen/Qwen2.5-VL-72B-Instruct": None,
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": None,
        "meta-llama/Llama-4-Scout-17B-16E-Instruct": None,
        "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo": None,
        "Qwen/Qwen3-235B-A22B-fp8-tput": None
    },
    # https://ai.google.dev/gemini-api/docs/models?hl=zh-cn#gemini-2.5-pro-preview-05-06

    "google":{
        "gemini-2.0-flash": 1048576,
        "gemini-2.5-flash": 1048576,
        "gemini-2.5-pro": 1048576,
    },
    # https://docs.anthropic.com/en/docs/about-claude/models/all-models
    
    "anthropic":{
        "claude-3-7-sonnet-latest": 200*1e3,
        "claude-opus-4-20250514": 200*1e3,
        "claude-sonnet-4-20250514": 200*1e3,
    },
    # https://platform.openai.com/docs/models
    
    "openai":{
        "gpt-4.1-2025-04-14": 1047576,
        "gpt-4.1-mini-2025-04-14": 1047576,
        "o4-mini-2025-04-16": 200000,
    },

}

def count_model_sources():
    """
    统计每个模型在多少个源（供应商）中可用
    
    考虑多模态模型和非多模态模型的映射关系：
    - 如果多模态模型值为None，则使用对应的非多模态模型
    - 统计每个模型实际可用的源数量
    
    返回:
    - model_source_count: 字典，格式为 {model_name: available_source_count}
    """
    # 获取所有模型列表
    all_models = set()
    all_models.update(model_list_normal)
    all_models.update(model_list_thinking) 
    all_models.update(model_list_mm_normal)
    all_models.update(model_list_mm_thinking)
    
    model_source_count = {}
    
    # 遍历每个模型
    for model_name in sorted(all_models):
        available_sources = []
        
        # 遍历每个源
        for source_name in source_mapping:
            # 获取基础模型名（去掉_mm后缀）
            base_model_name = model_name[:-3] if model_name.endswith("_mm") else model_name
            
            # 检查源是否支持这个模型
            if base_model_name in source_mapping[source_name]:
                source_model_name = source_mapping[source_name][base_model_name]
                
                # 如果多模态模型的值为None，检查是否有对应的非多模态版本
                if model_name.endswith("_mm") and source_model_name is None:
                    # 多模态模型值为None，使用基础模型的映射
                    if base_model_name in source_mapping[source_name] and source_mapping[source_name][base_model_name] is not None:
                        available_sources.append(source_name)
                elif source_model_name is not None:
                    # 直接可用
                    available_sources.append(source_name)
        
        model_source_count[model_name] = len(available_sources)
    
    return model_source_count

def print_model_source_statistics():
    """
    打印每个模型的源可用性统计信息
    
    按模型类型分组显示，并提供详细的统计信息
    """
    model_counts = count_model_sources()
    
    print("=" * 80)
    print("📊 模型源可用性统计报告")
    print("=" * 80)
    
    # 按模型类型分组
    model_groups = [
        ("非推理类大语言模型", model_list_normal),
        ("推理类大语言模型", model_list_thinking),
        ("非推理类多模态大模型", model_list_mm_normal), 
        ("推理类多模态大模型", model_list_mm_thinking)
    ]
    
    total_models = 0
    total_source_assignments = 0
    
    for group_name, model_list in model_groups:
        if not model_list:
            continue
            
        print(f"\n🔹 {group_name}")
        print("-" * 60)
        
        group_models = 0
        group_source_assignments = 0
        
        for model_name in model_list:
            source_count = model_counts.get(model_name, 0)
            group_models += 1
            group_source_assignments += source_count
            
            # 根据可用源数量显示不同的状态图标
            if source_count == 0:
                status = "❌"
            elif source_count == 1:
                status = "⚠️ "
            elif source_count <= 3:
                status = "✅"
            else:
                status = "🌟"
            
            print(f"  {status} {model_name:<25} -> {source_count} 个源")
        
        avg_sources = group_source_assignments / group_models if group_models > 0 else 0
        print(f"  📈 小计: {group_models} 个模型，平均 {avg_sources:.1f} 个源/模型")
        
        total_models += group_models
        total_source_assignments += group_source_assignments
    
    # 总体统计
    print("\n" + "=" * 80)
    print("📋 总体统计")
    print("=" * 80)
    
    avg_sources_overall = total_source_assignments / total_models if total_models > 0 else 0
    print(f"总模型数: {total_models}")
    print(f"总源分配数: {total_source_assignments}")
    print(f"平均源数/模型: {avg_sources_overall:.2f}")
    
    # 源覆盖率分析
    print(f"\n🔍 源覆盖率分析:")
    coverage_stats = {}
    for count in model_counts.values():
        coverage_stats[count] = coverage_stats.get(count, 0) + 1
    
    for source_count in sorted(coverage_stats.keys()):
        model_count = coverage_stats[source_count]
        percentage = (model_count / total_models) * 100 if total_models > 0 else 0
        
        if source_count == 0:
            status = "❌ 不可用"
        elif source_count == 1:
            status = "⚠️  单一源"
        elif source_count <= 3:
            status = "✅ 多源支持"
        else:
            status = "🌟 高可用性"
        
        print(f"  {status}: {model_count} 个模型 ({percentage:.1f}%) 在 {source_count} 个源中可用")
    
    # 多模态映射分析
    print(f"\n🔄 多模态模型映射分析:")
    mm_models = [m for m in model_counts.keys() if m.endswith("_mm")]
    mapped_count = 0
    
    for mm_model in mm_models:
        base_model = mm_model[:-3]
        mm_sources = model_counts[mm_model]
        base_sources = model_counts.get(base_model, 0)
        
        if mm_sources > 0 and base_sources > 0:
            # 检查是否使用了基础模型的映射
            using_base_mapping = False
            for source_name in source_mapping:
                if base_model in source_mapping[source_name]:
                    if source_mapping[source_name][base_model] is not None:
                        using_base_mapping = True
                        break
            
            if using_base_mapping:
                mapped_count += 1
    
    print(f"  📊 多模态模型总数: {len(mm_models)}")
    print(f"  🔗 使用基础模型映射: {mapped_count} 个")
    print(f"  📈 映射使用率: {(mapped_count/len(mm_models)*100):.1f}%" if mm_models else "0%")
    
    print("\n" + "=" * 80)
    print("✅ 统计完成")
    print("=" * 80)

def validate_mappings():
    """
    验证所有的模型列表和映射是否一致和互相包含
    
    检查:
    1. 所有模型列表中的模型都在source_mapping中
    2. 所有配置中的源是否一致(source_config, source_ranking, source_mapping, source_price, source_max_ioLength)
    3. 带有"_mm"后缀且值为None的模型应该有相应的非多模态版本
    4. source_price和source_max_ioLength的字段应完全一致
    5. source_price和source_max_ioLength中的模型应对应source_mapping中值不为None的模型
    6. 健康检测屏蔽清单中的模型必须存在于模型列表中
    
    返回:
    - errors: 发现的错误列表
    - warnings: 发现的警告列表
    """
    errors = []
    warnings = []
    
    # 1. 获取所有模型列表中的模型
    all_models = set()
    all_models.update(model_list_normal)
    all_models.update(model_list_thinking)
    all_models.update(model_list_mm_normal)
    all_models.update(model_list_mm_thinking)
    
    # 2. 检查源配置的一致性
    source_config_keys = set(source_config.keys())
    source_ranking_set = set(source_ranking)
    source_mapping_keys = set(source_mapping.keys())
    source_price_keys = set(source_price.keys())
    source_max_ioLength_keys = set(source_max_ioLength.keys())
    
    # 检查所有源配置中的源是否一致
    all_source_sets = [
        ("source_config", source_config_keys),
        ("source_ranking", source_ranking_set),
        ("source_mapping", source_mapping_keys),
        ("source_price", source_price_keys),
        ("source_max_ioLength", source_max_ioLength_keys)
    ]
    
    # 比较所有源集合的一致性
    for i, (name1, set1) in enumerate(all_source_sets):
        for name2, set2 in all_source_sets[i+1:]:
            if set1 != set2:
                missing = set2 - set1
                extra = set1 - set2
                if missing:
                    errors.append(f"源配置不一致: {name1}中缺少{name2}中的源: {missing}")
                if extra:
                    errors.append(f"源配置不一致: {name1}中有额外的{name2}中没有的源: {extra}")
    
    # 3. 检查每个源下是否有所有的模型
    for source, models_map in source_mapping.items():
        model_keys = set(models_map.keys())
        
        # 收集所有列表中的模型但在当前源映射中缺失的
        missing_models = all_models - model_keys
        if missing_models:
            errors.append(f"源 '{source}' 缺少模型: {missing_models}")
        
        # 收集当前源映射中有但不在任何模型列表中的
        extra_models = model_keys - all_models
        if extra_models:
            warnings.append(f"源 '{source}' 有额外的模型: {extra_models}")
    
    # 4. 检查_mm模型的特殊逻辑
    for source, models_map in source_mapping.items():
        for model_name, model_value in models_map.items():
            if model_name.endswith("_mm") and model_value is None:
                # 去掉_mm后缀获取基础模型名
                base_model_name = model_name[:-3]
                
                # 检查基础模型是否存在于该源
                if base_model_name not in models_map:
                    errors.append(f"源 '{source}' 中模型 '{model_name}' 值为None，但没有找到对应的基础模型 '{base_model_name}'")
    
    # 5. 检查source_price和source_max_ioLength的模型与source_mapping的一致性
    for source in source_mapping:
        if source not in source_price or source not in source_max_ioLength:
            continue  # 已在前面的检查中报告过错误
        
        # 获取当前源中有效的模型路径（不为None的值）
        valid_model_paths = {v for k, v in source_mapping[source].items() if v is not None}
        price_model_paths = set(source_price[source].keys())
        iolength_model_paths = set(source_max_ioLength[source].keys())
        
        # 检查source_price和source_max_ioLength中的模型是否一致
        if price_model_paths != iolength_model_paths:
            missing_in_price = iolength_model_paths - price_model_paths
            missing_in_iolength = price_model_paths - iolength_model_paths
            
            if missing_in_price:
                errors.append(f"源 '{source}' 中的模型在source_max_ioLength中存在但在source_price中缺失: {missing_in_price}")
            if missing_in_iolength:
                errors.append(f"源 '{source}' 中的模型在source_price中存在但在source_max_ioLength中缺失: {missing_in_iolength}")
                
        # 验证模型在source_mapping中存在，且对应的值不为None
        # 检查是否有模型在source_mapping中(不为None)但不在price和iolength中
        missing_price_models = valid_model_paths - price_model_paths
        if missing_price_models:
            errors.append(f"源 '{source}' 中的模型映射存在但缺少价格定义: {missing_price_models}")
            
        missing_iolength_models = valid_model_paths - iolength_model_paths
        if missing_iolength_models:
            errors.append(f"源 '{source}' 中的模型映射存在但缺少最大IO长度定义: {missing_iolength_models}")
        
        # 检查是否有模型在price和iolength中但不在source_mapping中(或在source_mapping中但为None)
        extra_price_models = price_model_paths - valid_model_paths
        if extra_price_models:
            errors.append(f"源 '{source}' 中定义了不存在于模型映射的价格: {extra_price_models}")
            
        extra_iolength_models = iolength_model_paths - valid_model_paths
        if extra_iolength_models:
            errors.append(f"源 '{source}' 中定义了不存在于模型映射的最大IO长度: {extra_iolength_models}")
        
        # 检查格式
        # 价格格式检查
        for model_path, price in source_price[source].items():
            if price is not None and not isinstance(price, (float, tuple)):
                errors.append(f"源 '{source}' 中模型 '{model_path}' 的价格格式错误: {price}，应为None, float或tuple")
            elif isinstance(price, tuple) and (len(price) != 2 or not all(isinstance(p, float) or p is None for p in price)):
                errors.append(f"源 '{source}' 中模型 '{model_path}' 的价格元组格式错误: {price}，应为(input_price, output_price)")
        
        # 最大IO长度格式检查
        for model_path, iolength in source_max_ioLength[source].items():
            if iolength is not None and not isinstance(iolength, (int, float)):
                errors.append(f"源 '{source}' 中模型 '{model_path}' 的最大IO长度格式错误: {iolength}，应为None, int或float")
    
    # 6. 检查健康检测屏蔽清单
    invalid_blacklisted_models = set(health_check_blacklist) - all_models
    if invalid_blacklisted_models:
        errors.append(f"健康检测屏蔽清单中包含不存在的模型: {invalid_blacklisted_models}")
    
    # 验证屏蔽清单中的模型至少在一个源上可用
    unavailable_blacklisted_models = []
    for model in health_check_blacklist:
        if model in all_models:
            # 检查模型是否在至少一个源上可用
            available_in_any_source = False
            for source, models_map in source_mapping.items():
                base_model_name = model[:-3] if model.endswith("_mm") else model
                if base_model_name in models_map and models_map[base_model_name] is not None:
                    available_in_any_source = True
                    break
            if not available_in_any_source:
                unavailable_blacklisted_models.append(model)
    
    if unavailable_blacklisted_models:
        warnings.append(f"健康检测屏蔽清单中的模型在任何源上都不可用: {unavailable_blacklisted_models}")
    
    return errors, warnings

if __name__ == "__main__":
    print("🔧 运行配置验证...")
    errors, warnings = validate_mappings()
    print_model_source_statistics()

