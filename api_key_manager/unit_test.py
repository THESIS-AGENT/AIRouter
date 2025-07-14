#!/usr/bin/env python3
import requests
import time
import hashlib
import json
import random
import argparse
import multiprocessing
from datetime import datetime, timedelta
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import logging

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_key_tester")

# 添加父目录到路径以导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ew_config.api_keys import pool_mapping

# 配置参数
API_BASE_URL = "http://localhost:8002"
SUCCESS_RATE = 0.7  # 70% 成功率，30% 失败率
TEST_ROUNDS = 10     # 每个源的测试轮次
MAX_RETRIES = 3      # 请求最大重试次数
RETRY_DELAY = 1.5    # 重试间隔时间（秒）
REQUEST_TIMEOUT = 15  # 请求超时时间（秒）

# 全局计数器，用于跟踪请求成功和失败情况
success_counter = 0
failure_counter = 0
counter_lock = threading.Lock()

# 限流器
class RateLimiter:
    def __init__(self, max_calls, period=1.0):
        """
        初始化限流器
        
        Args:
            max_calls: 在period秒内允许的最大调用次数
            period: 时间窗口大小（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()
        
    def __call__(self):
        """
        检查是否允许当前调用，并在允许时记录调用
        
        Returns:
            bool: 如果允许调用返回True，否则返回False
        """
        with self.lock:
            now = time.time()
            # 清理过期的调用记录
            self.calls = [t for t in self.calls if now - t < self.period]
            
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            return False
    
    def wait(self):
        """
        等待直到允许进行调用
        """
        while not self():
            time.sleep(0.1)

# 创建一个限流器，限制对API的请求速率
api_limiter = RateLimiter(max_calls=20, period=1.0)  # 每秒最多20个请求

def generate_request_id(prefix):
    """生成唯一的请求ID，基于时间戳和随机数的MD5哈希"""
    timestamp = datetime.now().isoformat()
    random_str = str(random.random())
    hash_input = f"{prefix}_{timestamp}_{random_str}"
    return hashlib.md5(hash_input.encode()).hexdigest()

def get_available_sources():
    """获取有效的可用源列表（过滤掉空的源）"""
    try:
        # 从配置中导入
        from ew_config.api_keys import pool_mapping
        from ew_config.source import source_mapping
        
        # 获取既在source_mapping中定义又有API密钥的源，并且API密钥池不为空
        available_sources = []
        for source in source_mapping.keys():
            if source in pool_mapping and pool_mapping[source]:
                # 检查是否有实际的API密钥
                has_keys = False
                for user_pool in pool_mapping[source].values():
                    if user_pool:  # 用户池不为空
                        has_keys = True
                        break
                if has_keys:
                    available_sources.append(source)
        
        logger.info(f"检测到可用源: {available_sources}")
        return available_sources
    except ImportError as e:
        logger.error(f"导入配置失败: {e}")
        return ["openai", "anthropic"]  # 默认源

def get_api_key(source_name):
    """获取指定源的API密钥"""
    # 等待限流器允许请求
    api_limiter.wait()
    
    url = f"{API_BASE_URL}/get_apikey"
    payload = {"source_name": source_name}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                return response.json()["api_key"]
            else:
                logger.error(f"获取API密钥失败 (尝试 {attempt+1}/{MAX_RETRIES}): {response.text}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常 (尝试 {attempt+1}/{MAX_RETRIES}): {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
    
    return None

def record_api_key_usage(api_key, source_name, model_name="gpt-4", status=True):
    """记录API密钥使用情况"""
    # 等待限流器允许请求
    api_limiter.wait()
    
    request_id = generate_request_id(source_name)
    create_time = datetime.now() - timedelta(minutes=random.randint(1, 5))
    finish_time = create_time + timedelta(seconds=random.uniform(1, 10))
    execution_time = (finish_time - create_time).total_seconds()
    
    url = f"{API_BASE_URL}/notice_apikey"
    payload = {
        "request_id": request_id,
        "api_key": api_key,
        "model_name": model_name,
        "source_name": source_name,
        "prompt_tokens": random.randint(100, 500),
        "completion_tokens": random.randint(50, 200),
        "create_time": create_time.isoformat(),
        "finish_time": finish_time.isoformat(),
        "execution_time": execution_time,
        "status": status
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 201:
                logger.info(f"记录API密钥使用情况成功: {request_id} {api_key[:10]}... 状态: {status}")
                return True
            else:
                logger.error(f"记录API密钥使用情况失败 (尝试 {attempt+1}/{MAX_RETRIES}): {response.text}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常 (尝试 {attempt+1}/{MAX_RETRIES}): {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
    
    logger.error(f"记录API密钥使用情况失败: 已达到最大重试次数")
    return False

def record_all_api_keys_usage():
    """记录所有源和所有API密钥的使用情况"""
    logger.info("=" * 80)
    logger.info(f"开始记录所有API密钥的使用情况...")
    logger.info("=" * 80)
    
    # 使用可用源列表
    available_sources = get_available_sources()
    
    for source_name in available_sources:
        if source_name not in pool_mapping:
            continue
            
        logger.info(f"\n测试源: {source_name}")
        logger.info("-" * 40)
        
        for user_name, api_keys in pool_mapping[source_name].items():
            logger.info(f"  用户: {user_name}")
            
            for api_key_info in api_keys:
                api_key = api_key_info["api_key"]
                key_name = api_key_info["name"]
                
                # 随机决定是成功还是失败
                status = random.random() < SUCCESS_RATE
                
                logger.info(f"    密钥 '{key_name}': ", end="")
                result = record_api_key_usage(api_key, source_name, status=status)
                if not result:
                    logger.info("  ❌ 记录失败")
                else:
                    logger.info("  ✅ 记录成功")
    
    logger.info("\n所有API密钥使用情况记录完成")

def test_api_key_rotation():
    """测试API密钥轮询"""
    logger.info("=" * 80)
    logger.info("测试API密钥轮询...")
    logger.info("=" * 80)
    
    # 使用可用源列表
    available_sources = get_available_sources()
    
    for source_name in available_sources:
        logger.info(f"\n源: {source_name}")
        logger.info("-" * 40)
        
        for i in range(TEST_ROUNDS):
            api_key = get_api_key(source_name)
            if api_key:
                logger.info(f"  轮次 {i+1}: 获取到API密钥: {api_key[:15]}...")
                
                # 随机决定是记录成功还是失败
                status = random.random() < SUCCESS_RATE
                record_api_key_usage(api_key, source_name, status=status)
                
                logger.info(f"    状态: {'成功' if status else '失败'}")
            else:
                logger.info(f"  轮次 {i+1}: 获取API密钥失败")
            
            # 短暂暂停，避免请求过快
            time.sleep(0.5)
    
    logger.info("\nAPI密钥轮询测试完成")

def worker_process(worker_id, num_requests, sources=None, req_queue=None, res_queue=None):
    """工作进程函数，模拟多个用户同时请求API密钥"""
    if sources is None:
        sources = get_available_sources()  # 使用过滤后的可用源
    
    local_success = 0
    local_failure = 0
    api_keys_used = {}
    
    logger.info(f"工作进程 {worker_id} 启动，将执行 {num_requests} 个请求")
    
    # 如果使用请求队列模式
    if req_queue is not None and res_queue is not None:
        for _ in range(num_requests):
            try:
                # 从队列中获取任务
                task = req_queue.get(timeout=1)
                source_name = task['source_name']
                
                # 获取API密钥
                api_key = get_api_key(source_name)
                if api_key:
                    # 记录使用的API密钥
                    if api_key not in api_keys_used:
                        api_keys_used[api_key] = 0
                    api_keys_used[api_key] += 1
                    
                    # 随机决定是成功还是失败
                    status = random.random() < SUCCESS_RATE
                    
                    # 记录API密钥使用情况
                    if record_api_key_usage(api_key, source_name, status=status):
                        if status:
                            local_success += 1
                        else:
                            local_failure += 1
                        logger.info(f"进程 {worker_id} - 请求: 源 {source_name} - 状态 {'成功' if status else '失败'}")
                    else:
                        local_failure += 1
                        logger.error(f"进程 {worker_id} - 请求: 记录使用情况失败")
                else:
                    local_failure += 1
                    logger.error(f"进程 {worker_id} - 请求: 获取API密钥失败")
                
                # 标记任务完成
                req_queue.task_done()
                
            except queue.Empty:
                # 队列为空，可能所有任务已分发完
                break
            except Exception as e:
                logger.error(f"工作进程 {worker_id} 处理任务时出错: {str(e)}")
                local_failure += 1
                if req_queue is not None:
                    req_queue.task_done()
            
            # 随机短暂延迟，模拟真实请求间隔
            time.sleep(random.uniform(0.1, 0.3))
    else:
        # 常规模式
        for i in range(num_requests):
            # 随机选择一个源
            source_name = random.choice(sources)
            
            # 获取API密钥
            api_key = get_api_key(source_name)
            if api_key:
                # 记录使用的API密钥
                if api_key not in api_keys_used:
                    api_keys_used[api_key] = 0
                api_keys_used[api_key] += 1
                
                # 随机决定是成功还是失败
                status = random.random() < SUCCESS_RATE
                
                # 记录API密钥使用情况
                if record_api_key_usage(api_key, source_name, status=status):
                    if status:
                        local_success += 1
                    else:
                        local_failure += 1
                    logger.info(f"进程 {worker_id} - 请求 {i+1}/{num_requests}: 源 {source_name} - 状态 {'成功' if status else '失败'}")
                else:
                    local_failure += 1
                    logger.error(f"进程 {worker_id} - 请求 {i+1}/{num_requests}: 记录使用情况失败")
            else:
                local_failure += 1
                logger.error(f"进程 {worker_id} - 请求 {i+1}/{num_requests}: 获取API密钥失败")
            
            # 随机短暂延迟，模拟真实请求间隔
            time.sleep(random.uniform(0.1, 0.3))
    
    results = {
        "worker_id": worker_id,
        "total": num_requests,
        "success": local_success,
        "failure": local_failure,
        "api_keys": api_keys_used
    }
    
    logger.info(f"工作进程 {worker_id} 完成，成功: {local_success}，失败: {local_failure}")
    
    # 如果使用结果队列，则将结果放入队列
    if res_queue is not None:
        res_queue.put(results)
    
    return results

def thread_worker(worker_id, num_requests, sources=None, req_queue=None, res_queue=None):
    """线程工作函数，用于多线程测试"""
    return worker_process(f"T{worker_id}", num_requests, sources, req_queue, res_queue)

def run_stress_test(num_processes, num_threads, requests_per_worker, sources=None, use_queues=False):
    """
    运行压力测试
    
    Args:
        num_processes: 进程数
        num_threads: 每个进程的线程数
        requests_per_worker: 每个工作线程的请求数
        sources: 要测试的源列表，如果为None则测试所有源
        use_queues: 是否使用队列进行任务分发，有助于限制并发量
    """
    logger.info("=" * 80)
    logger.info(f"开始压力测试: {num_processes}个进程，每个进程{num_threads}个线程，每个工作线程{requests_per_worker}个请求")
    logger.info("=" * 80)
    
    if sources is None:
        sources = get_available_sources()  # 使用过滤后的可用源
        logger.info(f"测试所有可用源: {', '.join(sources)}")
    else:
        # 过滤掉无效源
        valid_sources = []
        available_sources = get_available_sources()
        for source in sources:
            if source in available_sources:
                valid_sources.append(source)
            else:
                logger.warning(f"跳过无效源: {source}")
        sources = valid_sources
        logger.info(f"测试指定源: {', '.join(sources)}")
    
    if not sources:
        logger.error("没有可用的源进行测试！")
        return
    
    start_time = time.time()
    
    # 简化版本：只使用单进程多线程
    logger.info(f"使用单进程多线程模式进行测试")
    
    # 收集所有结果
    all_results = []
    
    # 创建所有工作线程
    total_workers = num_processes * num_threads
    with ThreadPoolExecutor(max_workers=total_workers) as executor:
        futures = []
        
        # 提交所有任务
        for p in range(num_processes):
            for t in range(num_threads):
                worker_id = f"P{p}-T{t}"
                future = executor.submit(worker_process, worker_id, requests_per_worker, sources, None, None)
                futures.append(future)
        
        # 收集结果
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                all_results.append(result)
                logger.info(f"完成工作线程 {i+1}/{total_workers}: {result['worker_id']}, 成功: {result['success']}, 失败: {result['failure']}")
            except Exception as e:
                    logger.error(f"工作线程执行出错: {str(e)}")
    
    end_time = time.time()
    total_time = end_time - start_time
    total_requests = num_processes * num_threads * requests_per_worker
    
    # 统计结果
    total_success = sum(result.get('success', 0) for result in all_results)
    total_failure = sum(result.get('failure', 0) for result in all_results)
    
    logger.info("\n" + "=" * 80)
    logger.info(f"压力测试完成！")
    logger.info(f"总请求数: {total_requests}")
    logger.info(f"成功请求: {total_success}")
    logger.info(f"失败请求: {total_failure}")
    logger.info(f"成功率: {total_success / (total_success + total_failure) * 100:.1f}%" if (total_success + total_failure) > 0 else "N/A")
    logger.info(f"总耗时: {total_time:.2f}秒")
    if total_time > 0:
        logger.info(f"平均请求速率: {total_requests / total_time:.2f}请求/秒")
        logger.info(f"实际处理速率: {(total_success + total_failure) / total_time:.2f}请求/秒")
    logger.info("=" * 80)

def monitor_queue(q, total_size, interval=5):
    """监控队列大小的线程函数"""
    start_time = time.time()
    while True:
        remaining = q.qsize()
        if remaining == 0:
            logger.info(f"队列处理完毕，耗时: {time.time() - start_time:.2f}秒")
            break
            
        percentage = 100 - (remaining / total_size * 100)
        logger.info(f"队列进度: {percentage:.1f}% (剩余: {remaining})")
        time.sleep(interval)

def run_threaded_workers(process_id, num_threads, requests_per_thread, sources, req_queue=None, res_queue=None):
    """在一个进程内运行多个线程"""
    logger.info(f"进程 {process_id} 启动 {num_threads} 个线程")
    
    thread_results = []
    thread_local_queue = queue.Queue() if res_queue is None else None
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for t in range(num_threads):
            future = executor.submit(
                thread_worker, 
                f"P{process_id}-T{t}", 
                requests_per_thread, 
                sources,
                req_queue,
                thread_local_queue if thread_local_queue is not None else res_queue
            )
            futures.append(future)
        
        # 收集结果
        for future in as_completed(futures):
            try:
                result = future.result()
                thread_results.append(result)
            except Exception as e:
                logger.error(f"线程执行出错: {str(e)}")
    
    # 如果使用了本地队列，将结果转移到进程间队列
    if thread_local_queue is not None and res_queue is not None:
        while not thread_local_queue.empty():
            try:
                result = thread_local_queue.get(timeout=1)
                res_queue.put(result)
            except queue.Empty:
                break
    
    # 如果有进程间队列，也将线程结果放入队列
    if res_queue is not None:
        for result in thread_results:
            res_queue.put(result)
    
    logger.info(f"进程 {process_id} 的所有线程已完成")
    return thread_results

def check_service_health():
    """检查API服务的健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("API服务健康状态正常")
            return True
        else:
            logger.error(f"API服务健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"无法连接到API服务: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='API密钥管理器测试工具')
    parser.add_argument('--mode', choices=['basic', 'rotation', 'stress'], default='stress',
                        help='测试模式: basic(基本测试), rotation(轮询测试), stress(压力测试)')
    parser.add_argument('--processes', type=int, default=4, help='压力测试的进程数')
    parser.add_argument('--threads', type=int, default=5, help='每个进程的线程数')
    parser.add_argument('--requests', type=int, default=10, help='每个工作线程的请求数')
    parser.add_argument('--sources', nargs='+', help='要测试的特定源，默认测试所有源')
    parser.add_argument('--rounds', type=int, default=10, help='轮询测试的轮次数')
    parser.add_argument('--use-queues', action='store_true', help='使用队列进行任务分发')
    
    args = parser.parse_args()
    
    # 根据命令行参数设置全局参数
    global TEST_ROUNDS
    TEST_ROUNDS = args.rounds
    
    logger.info(f"API密钥管理测试开始，模式: {args.mode}\n")
    
    # 检查服务健康状态
    if not check_service_health():
        logger.error("API服务不可用，测试终止")
        return
    
    if args.mode == 'basic':
        # 第一阶段：记录所有API密钥的使用情况
        record_all_api_keys_usage()
        
    elif args.mode == 'rotation':
        # 第二阶段：测试API密钥轮询
        test_api_key_rotation()
        
    elif args.mode == 'stress':
        # 第三阶段：压力测试
        run_stress_test(
            num_processes=args.processes,
            num_threads=args.threads,
            requests_per_worker=args.requests,
            sources=args.sources,
            use_queues=args.use_queues
        )
    
    logger.info("\nAPI密钥管理测试完成")

if __name__ == "__main__":
    # 设置多进程启动方法
    multiprocessing.set_start_method('spawn', force=True)
    main()
