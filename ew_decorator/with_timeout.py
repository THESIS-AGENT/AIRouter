import os
import signal
import functools
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import concurrent.futures
import threading
import inspect

# 定义 with_timeout 装饰器
def timeout_handler(signum, frame):
    """超时信号处理函数"""
    raise TimeoutError("操作超时")

def with_timeout(timeout_param=None, default_seconds=300):
    """函数超时装饰器
    
    修改为始终使用ThreadPoolExecutor实现超时功能，
    因为signal模块只能在主线程中使用。
    """
    def decorator(func):
        # 获取函数的参数信息
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            seconds = default_seconds
            
            if timeout_param:
                # 先检查kwargs中是否有该参数
                if timeout_param in kwargs:
                    seconds = kwargs[timeout_param]
                else:
                    # 如果kwargs中没有，尝试从位置参数中获取
                    param_names = list(sig.parameters.keys())
                    if timeout_param in param_names:
                        param_index = param_names.index(timeout_param)
                        if param_index < len(args):
                            seconds = args[param_index]
                        else:
                            # 如果位置参数中也没有，尝试从函数默认参数中获取
                            param = sig.parameters[timeout_param]
                            if param.default != inspect.Parameter.empty:
                                seconds = param.default
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(f"函数 {func.__name__} 执行超时（{seconds}秒）")
                
        return wrapper
    return decorator
