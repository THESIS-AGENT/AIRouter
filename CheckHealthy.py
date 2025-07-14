from ew_config.source import *
from ew_api.curl_infra import CurlInfra
from ew_api.openai_infra import OpenaiInfra
from api_key_manager.client import APIKeyManagerClient
from ew_config.logging_config import setup_optimized_logging, create_error_summary
from tqdm import tqdm
from fastapi import FastAPI, BackgroundTasks, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from collections import deque, defaultdict
import uvicorn
import os
import json
import logging
import uuid
import base64

# 使用优化的日志配置
logger = setup_optimized_logging(
    log_level=logging.INFO,
    console_format='simple',     # 控制台使用简洁格式
    file_format='structured',    # 文件使用结构化格式
    enable_file_logging=True,
    log_file='health_check.log'
)

app = FastAPI(title="API Health Check Service")

health_data = {}

# 最大储存多少次检查的历史, 先进先出, 后进添加在末尾. 默认储存100条.
MAX_WINDOW_SIZE = int(os.environ.get("MAX_WINDOW_SIZE", 100))
# 定时器设置: 每多少分钟检查一次状态. 默认15分钟检查一次.
CHECK_TIMER_SPAN = int(os.environ.get("CHECK_TIMER_SPAN", 30))
API_KEY_MANAGER_URL = os.environ.get("API_KEY_MANAGER_URL", "http://localhost:8002")
HEALTH_CHECK_TIMEOUT = int(os.environ.get("HEALTH_CHECK_TIMEOUT", 30))
# 多模态模型专用超时时间，默认60秒
HEALTH_CHECK_TIMEOUT_MM = int(os.environ.get("HEALTH_CHECK_TIMEOUT_MM", 60))

# 加载测试图片（用于多模态模型测试）
TEST_IMAGE_BASE64 = None
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test.jpg")

if os.path.exists(TEST_IMAGE_PATH):
    try:
        with open(TEST_IMAGE_PATH, "rb") as img_file:
            TEST_IMAGE_BASE64 = base64.b64encode(img_file.read()).decode("utf-8")
        logger.info(f"测试图片加载成功")
    except Exception as e:
        logger.warning(f"测试图片加载失败: {str(e)}")

def _is_commercial_error(error_message):
    """判断是否为商业性错误（如余额不足、配额超限等）
    
    Args:
        error_message (str): 错误消息
        
    Returns:
        bool: 如果是商业性错误返回True，技术性错误返回False
    """
    commercial_error_keywords = [
        "negative balance",
        "insufficient balance", 
        "quota exceeded",
        "insufficient_user_quota",
        "rate limit",
        "billing",
        "payment",
        "credit",
        "funds",
        "pre-payment",
        "subscription"
    ]
    
    error_lower = error_message.lower()
    return any(keyword in error_lower for keyword in commercial_error_keywords)

def _is_timeout_error(error_message):
    """判断是否为超时错误
    
    Args:
        error_message (str): 错误消息
        
    Returns:
        bool: 如果是超时错误返回True
    """
    timeout_keywords = [
        "timeout",
        "timed out",
        "execution timeout",
        "connection timeout",
        "read timeout",
        "request timeout",
        "执行超时",
        "连接超时",
        "请求超时",
        "响应超时"
    ]
    
    error_lower = error_message.lower()
    return any(keyword in error_lower for keyword in timeout_keywords)

def _get_error_level_and_message(error_message, error_type, source_name=None, model_name=None):
    """根据错误类型确定日志级别和消息
    
    Args:
        error_message (str): 错误消息
        error_type (str): 错误类型
        source_name (str): 源名称
        model_name (str): 模型名称
        
    Returns:
        tuple: (log_level, should_log, log_message)
            - log_level: 'ERROR', 'WARNING', 'DEBUG'
            - should_log: bool, 是否应该记录日志
            - log_message: str, 日志消息
    """
    # 创建简洁的错误摘要
    error_summary = create_error_summary(error_message, error_type, source_name, model_name)
    
    if _is_commercial_error(error_message):
        # 商业性错误：WARNING级别，不需要详细堆栈
        return 'WARNING', True, f"💰 {error_summary}"
    elif _is_timeout_error(error_message):
        # 超时错误：WARNING级别
        return 'WARNING', True, f"⏰ {error_summary}"
    elif "invalid.*api.*key" in error_message.lower():
        # API密钥错误：ERROR级别
        return 'ERROR', True, f"🔑 {error_summary}"
    else:
        # 其他技术性错误：ERROR级别
        return 'ERROR', True, f"🐛 {error_summary}"

def _build_multimodal_message(prompt, test_image_base64, source_name):
    """根据不同供应商构建正确格式的多模态消息
    
    Args:
        prompt (str): 文本提示
        test_image_base64 (str): Base64编码的测试图像
        source_name (str): 供应商名称
        
    Returns:
        tuple: (primary_messages, fallback_messages) 两种格式的消息
    """
    # 构建图像URL
    image_data_url = f"data:image/jpeg;base64,{test_image_base64}"
    
    # 对象格式（OpenAI等使用）
    object_format_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url}
                }
            ]
        }
    ]
    
    # 字符串格式（DeepInfra等使用）
    string_format_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": image_data_url  # 直接使用字符串，不是对象
                }
            ]
        }
    ]
    
    # 根据测试结果，大部分源都偏好对象格式
    # 只有极少数源可能需要字符串格式作为备用
    return object_format_messages, string_format_messages

class CheckHealthy:
    """测试所有源的所有模型, 返回一个执行时间.
    改造成异步定时任务."""
    
    @staticmethod
    def run():
        data_structure = {}
        logger.info("🏥 开始健康检查...")
        
        # 初始化API密钥管理器客户端
        api_key_client = APIKeyManagerClient(API_KEY_MANAGER_URL)
        
        # 统计计数器
        total_tests = 0
        success_count = 0
        error_count = 0
        
        try:
            # 获取所有模型列表
            all_models = model_list_normal + model_list_thinking + model_list_mm_normal + model_list_mm_thinking
            
            # 使用层级屏蔽逻辑过滤模型
            models_to_check = [model for model in all_models if not is_model_health_check_blacklisted(model)]
            blacklisted_models = [model for model in all_models if is_model_health_check_blacklisted(model)]
            
            if blacklisted_models:
                # 分析屏蔽原因
                exact_matches = [model for model in blacklisted_models if model in health_check_blacklist]
                hierarchical_matches = [model for model in blacklisted_models if model not in health_check_blacklist]
                
                logger.info(f"🚫 跳过健康检测的屏蔽模型: {', '.join(blacklisted_models)}")
                if exact_matches:
                    logger.info(f"  - 精确匹配屏蔽: {', '.join(exact_matches)}")
                if hierarchical_matches:
                    logger.info(f"  - 层级屏蔽(多模态): {', '.join(hierarchical_matches)}")
            
            logger.info(f"🏥 计划检测 {len(models_to_check)} 个模型，跳过 {len(blacklisted_models)} 个屏蔽模型")
            
            # 在自定义模型列表中遍历每个自定义模型名（排除屏蔽的模型）
            for model_name in tqdm(models_to_check, desc="健康检查"):
                # 在源-自定义模型名-源模型名的映射表中, 遍历每一个源
                for source_name in source_mapping:
                    try:
                        # 多模态模型和非多模态模型现在都是同一个模型名, 因此在我们这边, 靠自定义模型名后面的"_mm"来区别.
                        # 在源中, 通过自定义模型名, 或多模态大模型自定义模型名对应的自定义模型名, 来取回源模型名, 但源模型名是可能不存在的.
                        base_model_name = model_name[:-3] if model_name.endswith("_mm") else model_name
                        
                        # 检查源是否支持这个模型
                        if source_name not in source_mapping or base_model_name not in source_mapping[source_name]:
                            continue  # 跳过不支持的模型
                            
                        source_model_name = source_mapping[source_name][base_model_name]
                        
                        if source_model_name:
                            total_tests += 1
                            
                            start_time = datetime.now()
                            
                            # 跟据测试源配置文件, 获取test-api_key.
                            api_key = api_key_client.get_api_key(source_name)
                            if not api_key:
                                logger.warning(f"📭 无可用API密钥: {source_name}|{model_name}")
                                data_structure[f"{source_name}|{model_name}"] = None
                                error_count += 1
                                continue
                            
                            # 确定是否为多模态模型和对应的超时时间
                            is_multimodal = model_name.endswith("_mm")
                            timeout = HEALTH_CHECK_TIMEOUT_MM if is_multimodal else HEALTH_CHECK_TIMEOUT
                            
                            # 构建消息
                            if is_multimodal and TEST_IMAGE_BASE64:
                                prompt = "Describe this image in exactly 5 words"
                                primary_messages, fallback_messages = _build_multimodal_message(prompt, TEST_IMAGE_BASE64, source_name)
                            else:
                                # 非多模态模型使用文本消息
                                primary_messages = [{"role": "user", "content": "Hello!"}]
                                fallback_messages = primary_messages
                            
                            # 测试通过openai-api-sdk来连接源的模型.
                            if "openai" in source_config[source_name]:
                                source_config_openai = source_config[source_name]["openai"]
                                openai_infra = OpenaiInfra(source_config_openai, api_key)
                                try:
                                    # 健康检查使用较小的max_tokens以节省成本和时间
                                    health_check_params = {"max_tokens": 100}
                                    
                                    # 先尝试主要格式
                                    try:
                                        openai_result = openai_infra.get_response(primary_messages, [], source_model_name, timeout=timeout, additional_params=health_check_params)
                                    except Exception as primary_error:
                                        # 如果是多模态且格式错误，尝试备用格式
                                        if is_multimodal and "invalid type" in str(primary_error).lower():
                                            openai_result = openai_infra.get_response(fallback_messages, [], source_model_name, timeout=timeout, additional_params=health_check_params)
                                        else:
                                            raise primary_error
                                    
                                    end_time = datetime.now()
                                    if openai_result and "execution_time" in openai_result:
                                        execution_time = openai_result["execution_time"]
                                        data_structure[f"{source_name}|{model_name}"] = execution_time
                                        success_count += 1
                                        logger.debug(f"✅ {source_name}|{model_name} - {execution_time:.2f}s")
                                    else:
                                        # 如果没有返回结果或缺少execution_time，可能是隐性超时或API响应不完整
                                        execution_time = (end_time - start_time).total_seconds()
                                        data_structure[f"{source_name}|{model_name}"] = None
                                        error_count += 1
                                        
                                        # 记录为超时WARNING级别
                                        logger.warning(f"⏰ 无响应: {source_name}|{model_name} ({execution_time:.2f}s)", 
                                                      extra={
                                                          'source': source_name,
                                                          'model': model_name,
                                                          'api_type': 'OpenAI',
                                                          'timeout': timeout,
                                                          'execution_time': execution_time,
                                                          'error_type': 'NoResponse'
                                                      })
                                    request_id = str(uuid.uuid4())
                                    
                                    # 记录API密钥使用情况（成功）
                                    api_key_client.notice_api_key_usage(
                                        api_key=api_key,
                                        model_name=source_model_name,
                                        source_name=source_name,
                                        create_time=start_time,
                                        finish_time=end_time,
                                        execution_time=execution_time,
                                        status=True,
                                        prompt_tokens=openai_result.get("prompt_tokens"),
                                        completion_tokens=openai_result.get("completion_tokens"),
                                        request_id=request_id,
                                        remark="测试-健康监测"
                                    )
                                except Exception as e:
                                    end_time = datetime.now()
                                    execution_time = (end_time - start_time).total_seconds()
                                    request_id = str(uuid.uuid4())
                                    error_count += 1
                                    
                                    # 记录API密钥使用情况（失败）
                                    api_key_client.notice_api_key_usage(
                                        api_key=api_key,
                                        model_name=source_model_name,
                                        source_name=source_name,
                                        create_time=start_time,
                                        finish_time=end_time,
                                        execution_time=execution_time,
                                        status=False,
                                        request_id=request_id,
                                        remark="测试-健康监测"
                                    )
                                    
                                    # 根据错误类型确定日志级别和消息
                                    log_level, should_log, log_message = _get_error_level_and_message(
                                        str(e), type(e).__name__, source_name, model_name)
                                    
                                    if should_log:
                                        extra_info = {
                                            'source': source_name,
                                            'model': model_name,
                                            'api_type': 'OpenAI',
                                            'timeout': timeout,
                                            'error_type': type(e).__name__,
                                            'execution_time': execution_time
                                        }
                                        
                                        if log_level == 'ERROR':
                                            logger.error(log_message, extra=extra_info)
                                        elif log_level == 'WARNING':
                                            logger.warning(log_message, extra=extra_info)
                                        else:  # DEBUG
                                            logger.debug(log_message, extra=extra_info)
                                    data_structure[f"{source_name}|{model_name}"] = None
                                    
                            # 测试基于curl直连.
                            elif "curl" in source_config[source_name]:
                                source_config_curl = source_config[source_name]["curl"]
                                curl_infra = CurlInfra(source_config_curl, api_key)
                                try:
                                    # 健康检查使用较小的max_tokens以节省成本和时间
                                    health_check_params = {"max_tokens": 100}
                                    
                                    # 先尝试主要格式
                                    try:
                                        curl_result = curl_infra.get_response(primary_messages, [], source_model_name, timeout=timeout, additional_params=health_check_params)
                                    except Exception as primary_error:
                                        # 如果是多模态且格式错误，尝试备用格式
                                        if is_multimodal and "invalid type" in str(primary_error).lower():
                                            curl_result = curl_infra.get_response(fallback_messages, [], source_model_name, timeout=timeout, additional_params=health_check_params)
                                        else:
                                            raise primary_error
                                            
                                    end_time = datetime.now()
                                    if curl_result and "execution_time" in curl_result:
                                        execution_time = curl_result["execution_time"]
                                        data_structure[f"{source_name}|{model_name}"] = execution_time
                                        success_count += 1
                                        logger.debug(f"✅ {source_name}|{model_name} - {execution_time:.2f}s")
                                    else:
                                        # 如果没有返回结果或缺少execution_time，可能是隐性超时或API响应不完整
                                        execution_time = (end_time - start_time).total_seconds()
                                        data_structure[f"{source_name}|{model_name}"] = None
                                        error_count += 1
                                        
                                        # 记录为超时WARNING级别
                                        logger.warning(f"⏰ 无响应: {source_name}|{model_name} ({execution_time:.2f}s)", 
                                                      extra={
                                                          'source': source_name,
                                                          'model': model_name,
                                                          'api_type': 'CURL',
                                                          'timeout': timeout,
                                                          'execution_time': execution_time,
                                                          'error_type': 'NoResponse'
                                                      })
                                    request_id = str(uuid.uuid4())
                                    
                                    # 记录API密钥使用情况（成功）
                                    api_key_client.notice_api_key_usage(
                                        api_key=api_key,
                                        model_name=source_model_name,
                                        source_name=source_name,
                                        create_time=start_time,
                                        finish_time=end_time,
                                        execution_time=execution_time,
                                        status=True,
                                        prompt_tokens=curl_result.get("prompt_tokens"),
                                        completion_tokens=curl_result.get("completion_tokens"),
                                        request_id=request_id,
                                        remark="测试-健康监测"
                                    )
                                except Exception as e:
                                    end_time = datetime.now()
                                    execution_time = (end_time - start_time).total_seconds()
                                    request_id = str(uuid.uuid4())
                                    error_count += 1
                                    
                                    # 记录API密钥使用情况（失败）
                                    api_key_client.notice_api_key_usage(
                                        api_key=api_key,
                                        model_name=source_model_name,
                                        source_name=source_name,
                                        create_time=start_time,
                                        finish_time=end_time,
                                        execution_time=execution_time,
                                        status=False,
                                        request_id=request_id,
                                        remark="测试-健康监测"
                                    )
                                    
                                    # 根据错误类型确定日志级别和消息
                                    log_level, should_log, log_message = _get_error_level_and_message(
                                        str(e), type(e).__name__, source_name, model_name)
                                    
                                    if should_log:
                                        extra_info = {
                                            'source': source_name,
                                            'model': model_name,
                                            'api_type': 'CURL',
                                            'timeout': timeout,
                                            'error_type': type(e).__name__,
                                            'execution_time': execution_time
                                        }
                                        
                                        if log_level == 'ERROR':
                                            logger.error(log_message, extra=extra_info)
                                        elif log_level == 'WARNING':
                                            logger.warning(log_message, extra=extra_info)
                                        else:  # DEBUG
                                            logger.debug(log_message, extra=extra_info)
                                    data_structure[f"{source_name}|{model_name}"] = None
                    except Exception as e:
                        logger.error(f"🔧 处理失败: {source_name}|{model_name} - {create_error_summary(str(e), type(e).__name__, source_name, model_name)}")
                        data_structure[f"{source_name}|{model_name}"] = None
                        error_count += 1
            
            # 生成详细的汇总报告
            _generate_health_check_summary_report(total_tests, success_count, error_count, data_structure)
            
        except Exception as e:
            logger.error(f"💥 健康检查总体错误: {create_error_summary(str(e), type(e).__name__, None, None)}")
            
        return data_structure

def _generate_health_check_summary_report(total_tests: int, success_count: int, error_count: int, data_structure: dict):
    """生成健康检查的详细汇总报告"""
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    logger.info("🏥 ==================== 健康检查汇总报告 ====================")
    logger.info(f"🏥 总测试数: {total_tests}")
    logger.info(f"🏥 成功数: {success_count}")
    logger.info(f"🏥 失败数: {error_count}")
    logger.info(f"🏥 成功率: {success_rate:.1f}%")
    
    # 按源统计
    source_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0, 'avg_time': 0, 'models': set()})
    
    for key, value in data_structure.items():
        if '|' in key:
            source_name, model_name = key.split('|', 1)
            source_stats[source_name]['total'] += 1
            source_stats[source_name]['models'].add(model_name)
            
            if value is not None:
                source_stats[source_name]['success'] += 1
                source_stats[source_name]['avg_time'] += value
            else:
                source_stats[source_name]['failed'] += 1
    
    # 计算平均时间
    for stats in source_stats.values():
        if stats['success'] > 0:
            stats['avg_time'] = stats['avg_time'] / stats['success']
    
    # 按成功率排序显示源统计
    sorted_sources = sorted(source_stats.items(), 
                          key=lambda x: (x[1]['success'] / x[1]['total'] if x[1]['total'] > 0 else 0), 
                          reverse=True)
    
    logger.info("🏥 各源详细统计:")
    for source_name, stats in sorted_sources:
        source_success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        logger.info(f"🏥   [{source_name}]: {stats['success']}/{stats['total']} 成功 ({source_success_rate:.1f}%)")
        if stats['success'] > 0:
            logger.info(f"🏥     - 平均响应时间: {stats['avg_time']:.2f}s")
        logger.info(f"🏥     - 支持模型数: {len(stats['models'])}")
        
        # 显示失败模型（如果有）
        failed_models = []
        for model_name in stats['models']:
            key = f"{source_name}|{model_name}"
            if data_structure.get(key) is None:
                failed_models.append(model_name)
        
        if failed_models:
            models_display = ', '.join(failed_models[:5])
            if len(failed_models) > 5:
                models_display += f"... (共{len(failed_models)}个)"
            logger.info(f"🏥     - 失败模型: {models_display}")
    
    # 最快和最慢的模型
    successful_models = [(k, v) for k, v in data_structure.items() if v is not None]
    if successful_models:
        fastest = min(successful_models, key=lambda x: x[1])
        slowest = max(successful_models, key=lambda x: x[1])
        logger.info(f"🏥 最快响应: {fastest[0]} ({fastest[1]:.2f}s)")
        logger.info(f"🏥 最慢响应: {slowest[0]} ({slowest[1]:.2f}s)")
    
    logger.info("🏥 ===============================================================")

def update_health_data():
    """Run the health check and update the sliding window data"""
    logger.debug(f"[{datetime.now()}] 开始定时健康检查...")
    try:
        new_data = CheckHealthy.run()
        
        # Update sliding window for each key
        for key, value in new_data.items():
            if key not in health_data:
                health_data[key] = deque(maxlen=MAX_WINDOW_SIZE)
            
            health_data[key].append(value)
        
        logger.debug(f"[{datetime.now()}] 健康检查完成，更新了 {len(new_data)} 个指标")
    except Exception as e:
        logger.error(f"健康检查数据更新失败: {str(e)}")

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    update_health_data,
    trigger=IntervalTrigger(minutes=CHECK_TIMER_SPAN),
    id="health_check_job",
    name=f"Run API health check every {CHECK_TIMER_SPAN} minutes",
    replace_existing=True,
    max_instances=1,  # 确保只有一个实例在运行
    misfire_grace_time=300  # 如果错过了执行时间，5分钟内仍然会执行
)

@app.on_event("startup")
async def startup_event():
    """Run initial health check and start the scheduler"""
    logger.info("API健康检查服务正在启动...")
    
    # 初始化空数据，确保API立即可用
    all_models = model_list_normal + model_list_thinking + model_list_mm_normal + model_list_mm_thinking
    for model_name in all_models:
        for source_name in source_mapping:
            key = f"{source_name}|{model_name}"
            if key not in health_data:
                health_data[key] = deque(maxlen=MAX_WINDOW_SIZE)
                
    # 为屏蔽模型初始化空的健康数据结构，确保LoadBalancing能正常识别它们为无健康数据状态
    blacklisted_models = [model for model in all_models if is_model_health_check_blacklisted(model)]
    if blacklisted_models:
        logger.info(f"🚫 为 {len(blacklisted_models)} 个屏蔽模型初始化空健康数据结构（支持层级屏蔽）")
    
    # Start the scheduler
    scheduler.start()
    logger.info("健康检查调度器已启动")
    
    # 在后台运行初始健康检查，不阻塞API启动
    logger.info("正在后台启动初始健康检查...")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the scheduler when the app stops and save health data to a local file"""
    logger.info("服务关闭中，保存健康检查数据...")
    
    # Convert deque objects to lists for JSON serialization
    result = {k: list(v) for k, v in health_data.items()}
    
    # Create data object with timestamp
    data_to_save = {
        "timestamp": datetime.now().isoformat(),
        "check_timer_span": CHECK_TIMER_SPAN,
        "data": result
    }
    
    # Create directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Save to file with timestamp in filename
    filename = f"data/health_check_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(data_to_save, f, indent=2)
    
    logger.info(f"健康检查数据已保存到 {filename}")
    
    # Shutdown the scheduler
    scheduler.shutdown()
    logger.info("健康检查调度器已关闭")

@app.get("/check_healthy")
async def get_health_data():
    """Return the sliding window data for all API checks"""
    logger.debug("接收到健康检查数据请求")
    # Convert deque objects to lists for JSON serialization
    result = {k: list(v) for k, v in health_data.items()}
    return {
        "timestamp": datetime.now().isoformat(),
        "check_timer_span": CHECK_TIMER_SPAN,
        "data": result
    }

# Add a manual trigger endpoint for testing
@app.post("/trigger_health_check")
async def trigger_health_check(background_tasks: BackgroundTasks):
    """Manually trigger a health check (runs in background)"""
    logger.info("收到手动触发健康检查请求")
    background_tasks.add_task(update_health_data)
    return {"status": "健康检查已在后台触发"}

@app.get("/docker-health")
async def docker_health_check():
    """专门为Docker健康检查设计的端点，验证服务是否正常运行"""
    try:
        # 检查API Key Manager服务可用性
        api_key_client = APIKeyManagerClient(API_KEY_MANAGER_URL)
        
        # 尝试简单连接，如果能获取到一个API key就认为服务运行正常
        test_key = api_key_client.get_api_key("openai")
        
        # 即使没有获取到有效的key，只要没有抛出异常就认为服务可用
        logger.debug("Docker健康检查通过")
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Docker健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

if __name__ == "__main__":
    # Only use this for local development
    # In production, use the proper Docker setup
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")