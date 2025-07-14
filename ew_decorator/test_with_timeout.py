import time
import unittest
import sys
from pathlib import Path

# 导入with_timeout装饰器
sys.path.insert(0, str(Path(__file__).parent))
from with_timeout import with_timeout

# 定义一些测试函数
@with_timeout(timeout_param='timeout')
def function_with_param_timeout(timeout=None, sleep_time=1):
    """使用带有timeout参数的函数"""
    time.sleep(sleep_time)
    return "正常完成"

@with_timeout()
def function_with_default_timeout(sleep_time=1):
    """使用默认超时值的函数"""
    time.sleep(sleep_time)
    return "正常完成"

@with_timeout(default_seconds=2)
def function_with_custom_default(sleep_time=1):
    """使用自定义默认超时值的函数"""
    time.sleep(sleep_time)
    return "正常完成"

@with_timeout(timeout_param='custom_timeout_name')
def function_with_custom_param_name(sleep_time=1, custom_timeout_name=None):
    """使用自定义超时参数名的函数"""
    time.sleep(sleep_time)
    return "正常完成"

class TestWithTimeout(unittest.TestCase):
    
    def test_normal_execution(self):
        """测试正常执行情况"""
        # 调用函数，sleep时间小于超时时间
        result = function_with_param_timeout(timeout=2, sleep_time=1)
        self.assertEqual(result, "正常完成")
        
    def test_timeout_exception(self):
        """测试超时情况，应该引发TimeoutError"""
        # 调用函数，sleep时间大于超时时间
        with self.assertRaises(TimeoutError):
            function_with_param_timeout(timeout=1, sleep_time=2)
    
    def test_default_timeout(self):
        """测试默认超时参数"""
        # 默认超时值是120秒，所以这应该正常完成
        result = function_with_default_timeout(sleep_time=0.5)
        self.assertEqual(result, "正常完成")
    
    def test_custom_default_timeout(self):
        """测试自定义默认超时值"""
        # 自定义默认超时值为2秒，所以这应该正常完成
        result = function_with_custom_default(sleep_time=1)
        self.assertEqual(result, "正常完成")
        
        # 这应该超时
        with self.assertRaises(TimeoutError):
            function_with_custom_default(sleep_time=3)
    
    def test_custom_param_name(self):
        """测试自定义参数名"""
        # 使用自定义参数名，应该正常完成
        result = function_with_custom_param_name(sleep_time=1, custom_timeout_name=2)
        self.assertEqual(result, "正常完成")
        
        # 应该超时
        with self.assertRaises(TimeoutError):
            function_with_custom_param_name(sleep_time=3, custom_timeout_name=2)

if __name__ == "__main__":
    # 运行测试
    unittest.main() 