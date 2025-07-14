import logging
import re
import json
from datetime import datetime


class SmartLogFilter(logging.Filter):
    """智能日志过滤器，用于清理和简化日志消息"""
    
    def __init__(self):
        super().__init__()
        # 编译正则表达式以提高性能
        self.base64_pattern = re.compile(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]{50,}')
        self.long_json_pattern = re.compile(r'\{[^{}]{200,}\}')
        self.traceback_pattern = re.compile(r'Traceback \(most recent call last\):.*?(?=\n\w|\n$|\Z)', re.DOTALL)
    
    def filter(self, record):
        """过滤和清理日志记录"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # 移除base64图像数据
            record.msg = self.base64_pattern.sub('[IMAGE_DATA]', record.msg)
            
            # 缩短过长的JSON数据
            record.msg = self.long_json_pattern.sub('[LARGE_JSON_DATA]', record.msg)
            
            # 简化错误堆栈（保留最后一行错误信息）
            if 'Traceback' in record.msg:
                match = self.traceback_pattern.search(record.msg)
                if match:
                    full_traceback = match.group(0)
                    lines = full_traceback.split('\n')
                    # 保留最后的错误行
                    error_line = next((line for line in reversed(lines) if line.strip() and not line.startswith(' ')), '')
                    record.msg = self.traceback_pattern.sub(f'[TRACEBACK_SIMPLIFIED]: {error_line}', record.msg)
        
        return True


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname_colored = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        else:
            record.levelname_colored = record.levelname
        
        # 格式化时间
        record.formatted_time = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器，输出JSON格式"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外的上下文信息
        if hasattr(record, 'source'):
            log_obj['source'] = record.source
        if hasattr(record, 'model'):
            log_obj['model'] = record.model
        if hasattr(record, 'api_type'):
            log_obj['api_type'] = record.api_type
        if hasattr(record, 'error_type'):
            log_obj['error_type'] = record.error_type
        if hasattr(record, 'execution_time'):
            log_obj['execution_time'] = record.execution_time
        
        return json.dumps(log_obj, ensure_ascii=False)


def setup_optimized_logging(
    log_level=logging.INFO,
    console_format='simple',  # 'simple', 'detailed', 'structured'
    file_format='structured',
    enable_file_logging=True,
    log_file='health_check.log'
):
    """
    设置优化的日志配置
    
    Args:
        log_level: 日志级别
        console_format: 控制台输出格式 ('simple', 'detailed', 'structured')
        file_format: 文件输出格式 ('simple', 'detailed', 'structured')
        enable_file_logging: 是否启用文件日志
        log_file: 日志文件名
    """
    
    # 获取根logger
    logger = logging.getLogger("api_health_check")
    logger.setLevel(log_level)
    
    # 防止日志向上传播，避免重复打印
    logger.propagate = False
    
    # 清除现有的handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建智能过滤器
    smart_filter = SmartLogFilter()
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.addFilter(smart_filter)
    
    # 根据格式选择formatter
    if console_format == 'simple':
        console_formatter = ColoredFormatter(
            '%(formatted_time)s [%(levelname_colored)s] %(message)s'
        )
    elif console_format == 'detailed':
        console_formatter = ColoredFormatter(
            '%(formatted_time)s [%(levelname_colored)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    else:  # structured
        console_formatter = StructuredFormatter()
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 设置文件处理器
    if enable_file_logging:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.addFilter(smart_filter)
        
        if file_format == 'simple':
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            )
        elif file_format == 'detailed':
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
            )
        else:  # structured
            file_formatter = StructuredFormatter()
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 减少第三方库的日志噪音
    for lib_name in ['httpx', 'openai', 'apscheduler', 'uvicorn', 'uvicorn.access']:
        third_party_logger = logging.getLogger(lib_name)
        third_party_logger.setLevel(logging.ERROR)
        third_party_logger.propagate = False
    
    return logger


def create_error_summary(error_message, error_type, source_name=None, model_name=None):
    """
    创建简洁的错误摘要
    
    Args:
        error_message: 原始错误消息
        error_type: 错误类型
        source_name: 源名称
        model_name: 模型名称
    
    Returns:
        简洁的错误摘要
    """
    # 常见错误模式和对应的简洁描述
    error_patterns = {
        r'quota.*not enough|insufficient.*quota|insufficient_user_quota': '配额不足',
        r'invalid.*api.*key|incorrect.*api.*key': 'API密钥无效',
        r'timeout|timed out': '请求超时',
        r'connection.*refused|connection.*failed': '连接失败',
        r'rate.*limit|too many requests': '请求限流',
        r'model.*not.*found|model.*unavailable': '模型不可用',
        r'unauthorized|authentication.*failed': '认证失败',
        r'bad.*request|invalid.*request': '请求格式错误',
        r'server.*error|internal.*error': '服务器内部错误'
    }
    
    # 尝试匹配错误模式
    error_lower = error_message.lower()
    for pattern, description in error_patterns.items():
        if re.search(pattern, error_lower):
            summary = f"{description}"
            if source_name and model_name:
                summary += f" [{source_name}|{model_name}]"
            return summary
    
    # 如果没有匹配到模式，返回错误类型
    summary = f"未知错误: {error_type}"
    if source_name and model_name:
        summary += f" [{source_name}|{model_name}]"
    
    return summary 