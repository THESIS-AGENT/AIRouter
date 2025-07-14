import time
import functools

# 定义 counting_time 装饰器
def counting_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 如果结果是字典，添加执行时间作为key-value
        if isinstance(result, dict):
            result["execution_time"] = execution_time
        
        return result
    return wrapper