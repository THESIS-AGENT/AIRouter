"""
外部Web API LLM封装工具

提供统一的LLM调用接口，支持多源负载均衡和故障转移。

主要功能:
- LLM_Wrapper: LLM包装器，提供统一的接口调用不同源的模型
  - generate: 生成文本响应
  - generate_mm: 多模态生成（支持图像输入）
  - function_calling: 函数调用功能
"""

# 只导入需要对外暴露的类
from .LLMwrapper import LLM_Wrapper

# 导出的类和函数
__all__ = [
    'LLM_Wrapper',
]

# 版本信息
__version__ = '1.0.0' 