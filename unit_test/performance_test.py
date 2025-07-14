#!/usr/bin/env python3
"""
性能测试脚本：专注于测试系统的性能、稳定性和极限
"""

import time
import json
import base64
import os
import concurrent.futures
import statistics
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random
import threading

from LLMwrapper import LLM_Wrapper
from LoadBalancing import LoadBalancing
from ew_config.source import (
    model_list_normal, 
    model_list_thinking, 
    model_list_mm_normal,
    model_list_function_calling
)

# 测试配置
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test.jpg")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "performance_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

class PerformanceMetrics:
    """性能指标收集器"""
    def __init__(self):
        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        self.lock = threading.Lock()
    
    def add_metric(self, test_name: str, metric_name: str, value: float):
        with self.lock:
            if test_name not in self.metrics["tests"]:
                self.metrics["tests"][test_name] = {}
            if metric_name not in self.metrics["tests"][test_name]:
                self.metrics["tests"][test_name][metric_name] = []
            self.metrics["tests"][test_name][metric_name].append(value)
    
    def calculate_summary(self):
        """计算汇总统计"""
        for test_name, metrics in self.metrics["tests"].items():
            self.metrics["summary"][test_name] = {}
            for metric_name, values in metrics.items():
                if values:
                    self.metrics["summary"][test_name][metric_name] = {
                        "count": len(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "min": min(values),
                        "max": max(values),
                        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                        "p95": statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
                        "p99": statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)
                    }
    
    def save(self, filename: str):
        self.calculate_summary()
        filepath = os.path.join(RESULTS_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(self.metrics, f, indent=2)
        print(f"性能测试结果已保存到: {filepath}")
    
    def plot_results(self, filename: str):
        """生成性能图表"""
        self.calculate_summary()
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Performance Test Results', fontsize=16)
        
        # 响应时间分布
        ax1 = axes[0, 0]
        for test_name, metrics in self.metrics["tests"].items():
            if "response_time" in metrics:
                ax1.hist(metrics["response_time"], alpha=0.5, label=test_name, bins=20)
        ax1.set_xlabel('Response Time (seconds)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Response Time Distribution')
        ax1.legend()
        
        # 成功率趋势
        ax2 = axes[0, 1]
        for test_name, metrics in self.metrics["tests"].items():
            if "success" in metrics:
                # 计算滑动窗口成功率
                window_size = 10
                success_values = metrics["success"]
                if len(success_values) >= window_size:
                    success_rates = []
                    for i in range(len(success_values) - window_size + 1):
                        window = success_values[i:i+window_size]
                        success_rates.append(sum(window) / len(window) * 100)
                    ax2.plot(success_rates, label=test_name)
        ax2.set_xlabel('Time Window')
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_title('Success Rate Trend')
        ax2.legend()
        
        # 吞吐量
        ax3 = axes[1, 0]
        throughput_data = []
        labels = []
        for test_name, summary in self.metrics["summary"].items():
            if "throughput" in summary:
                throughput_data.append(summary["throughput"]["mean"])
                labels.append(test_name)
        if throughput_data:
            ax3.bar(labels, throughput_data)
            ax3.set_ylabel('Requests/Second')
            ax3.set_title('Average Throughput')
            ax3.tick_params(axis='x', rotation=45)
        
        # P95延迟
        ax4 = axes[1, 1]
        p95_data = []
        labels = []
        for test_name, summary in self.metrics["summary"].items():
            if "response_time" in summary:
                p95_data.append(summary["response_time"]["p95"])
                labels.append(test_name)
        if p95_data:
            ax4.bar(labels, p95_data, color='orange')
            ax4.set_ylabel('P95 Latency (seconds)')
            ax4.set_title('P95 Response Time')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plot_path = os.path.join(RESULTS_DIR, filename)
        plt.savefig(plot_path)
        print(f"Performance charts saved to: {plot_path}")

# ==================== 性能测试函数 ====================

def test_response_time_distribution(metrics: PerformanceMetrics, num_samples: int = 50):
    """测试响应时间分布"""
    print(f"\n=== 响应时间分布测试 ({num_samples} 个样本) ===")
    
    models = ["gpt41_normal", "gemini20_flash", "llama4_maverick"]
    prompts = [
        "What is 2+2?",
        "Explain quantum physics in simple terms",
        "Write a short poem about technology",
        "List the planets in our solar system",
        "What are the benefits of exercise?"
    ]
    
    for model in models:
        print(f"\n测试模型: {model}")
        response_times = []
        
        for i in range(num_samples):
            prompt = random.choice(prompts)
            try:
                start_time = time.time()
                response = LLM_Wrapper.generate(
                    model_name=model,
                    prompt=prompt,
                    mode="fast_first",
                    timeout=30
                )
                elapsed_time = time.time() - start_time
                response_times.append(elapsed_time)
                metrics.add_metric(f"response_time_{model}", "response_time", elapsed_time)
                metrics.add_metric(f"response_time_{model}", "success", 1)
                
                if i % 10 == 0:
                    print(f"  进度: {i}/{num_samples}, 平均响应时间: {statistics.mean(response_times):.2f}s")
            except Exception as e:
                metrics.add_metric(f"response_time_{model}", "success", 0)
                print(f"  错误: {str(e)[:50]}")
        
        if response_times:
            print(f"  完成 - 平均: {statistics.mean(response_times):.2f}s, P95: {statistics.quantiles(response_times, n=20)[18]:.2f}s")

def test_concurrent_load(metrics: PerformanceMetrics, num_workers: int = 10, duration: int = 60):
    """测试并发负载"""
    print(f"\n=== 并发负载测试 ({num_workers} 个工作线程, {duration} 秒) ===")
    
    models = ["gpt41_normal", "gemini20_flash", "llama4_maverick", "claude37_normal"]
    request_counter = {"count": 0, "success": 0, "error": 0}
    counter_lock = threading.Lock()
    stop_event = threading.Event()
    
    def worker(worker_id: int):
        """工作线程函数"""
        local_count = 0
        local_success = 0
        local_error = 0
        
        while not stop_event.is_set():
            model = random.choice(models)
            prompt = f"Worker {worker_id} request {local_count}: What is {random.randint(1, 100)} + {random.randint(1, 100)}?"
            
            try:
                start_time = time.time()
                response = LLM_Wrapper.generate(
                    model_name=model,
                    prompt=prompt,
                    mode="fast_first",
                    timeout=20
                )
                elapsed_time = time.time() - start_time
                
                metrics.add_metric("concurrent_load", "response_time", elapsed_time)
                metrics.add_metric("concurrent_load", "success", 1)
                local_success += 1
            except Exception as e:
                metrics.add_metric("concurrent_load", "success", 0)
                local_error += 1
            
            local_count += 1
            
            # 更新全局计数器
            with counter_lock:
                request_counter["count"] += 1
                request_counter["success"] += local_success
                request_counter["error"] += local_error
                local_success = 0
                local_error = 0
    
    # 启动工作线程
    threads = []
    start_time = time.time()
    
    for i in range(num_workers):
        thread = threading.Thread(target=worker, args=(i,))
        thread.start()
        threads.append(thread)
    
    # 运行指定时间
    print("测试进行中...")
    for i in range(duration):
        time.sleep(1)
        with counter_lock:
            elapsed = time.time() - start_time
            rate = request_counter["count"] / elapsed
            print(f"  时间: {i+1}/{duration}s, 总请求: {request_counter['count']}, 速率: {rate:.2f} req/s")
    
    # 停止工作线程
    stop_event.set()
    for thread in threads:
        thread.join()
    
    # 计算最终统计
    total_time = time.time() - start_time
    with counter_lock:
        total_requests = request_counter["count"]
        total_success = request_counter["success"]
        total_errors = request_counter["error"]
    
    throughput = total_requests / total_time
    success_rate = total_success / total_requests if total_requests > 0 else 0
    
    metrics.add_metric("concurrent_load", "throughput", throughput)
    metrics.add_metric("concurrent_load", "total_requests", total_requests)
    metrics.add_metric("concurrent_load", "success_rate", success_rate)
    
    print(f"\n并发测试完成:")
    print(f"  总请求数: {total_requests}")
    print(f"  成功率: {success_rate*100:.1f}%")
    print(f"  吞吐量: {throughput:.2f} req/s")

def test_model_switching_overhead(metrics: PerformanceMetrics):
    """测试模型切换开销"""
    print("\n=== 模型切换开销测试 ===")
    
    # 测试相同模型连续调用
    print("\n1. 相同模型连续调用")
    model = "gpt41_normal"
    same_model_times = []
    
    for i in range(10):
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=f"Test {i}",
                mode="fast_first",
                timeout=20
            )
            elapsed_time = time.time() - start_time
            same_model_times.append(elapsed_time)
            metrics.add_metric("same_model_switching", "response_time", elapsed_time)
        except Exception as e:
            print(f"  错误: {str(e)[:50]}")
    
    if same_model_times:
        print(f"  平均响应时间: {statistics.mean(same_model_times):.2f}s")
    
    # 测试不同模型切换
    print("\n2. 不同模型切换调用")
    models = ["gpt41_normal", "gemini20_flash", "llama4_maverick", "claude37_normal"]
    different_model_times = []
    
    for i in range(10):
        model = models[i % len(models)]
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=f"Test {i}",
                mode="fast_first",
                timeout=20
            )
            elapsed_time = time.time() - start_time
            different_model_times.append(elapsed_time)
            metrics.add_metric("different_model_switching", "response_time", elapsed_time)
        except Exception as e:
            print(f"  错误: {str(e)[:50]}")
    
    if different_model_times:
        print(f"  平均响应时间: {statistics.mean(different_model_times):.2f}s")
    
    # 测试帕累托选择开销
    print("\n3. 帕累托选择开销")
    pareto_times = []
    model_groups = [
        ["gpt41_normal", "gemini20_flash"],
        ["llama4_maverick", "claude37_normal", "gpt41_normal"],
        ["gemini20_flash", "llama4_maverick", "gemini25_flash", "claude37_normal"]
    ]
    
    for i in range(10):
        models = model_groups[i % len(model_groups)]
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate_fromTHEbest(
                model_list=models,
                prompt=f"Test {i}",
                mode="fast_first",
                timeout=20
            )
            elapsed_time = time.time() - start_time
            pareto_times.append(elapsed_time)
            metrics.add_metric("pareto_selection", "response_time", elapsed_time)
        except Exception as e:
            print(f"  错误: {str(e)[:50]}")
    
    if pareto_times:
        print(f"  平均响应时间: {statistics.mean(pareto_times):.2f}s")

def test_error_recovery(metrics: PerformanceMetrics):
    """测试错误恢复能力"""
    print("\n=== 错误恢复测试 ===")
    
    # 测试超时恢复
    print("\n1. 超时恢复测试")
    timeout_tests = []
    
    for timeout in [5, 10, 20]:
        print(f"\n  测试超时设置: {timeout}秒")
        for i in range(3):  # 减少测试次数
            try:
                start_time = time.time()
                # 使用一个适中的提示来测试超时
                response = LLM_Wrapper.generate(
                    model_name="claude37_normal",
                    prompt="Write a 200-word summary about artificial intelligence.",
                    mode="fast_first",
                    timeout=timeout
                )
                elapsed_time = time.time() - start_time
                timeout_tests.append({"timeout": timeout, "success": True, "time": elapsed_time})
                metrics.add_metric(f"timeout_recovery_{timeout}s", "success", 1)
                metrics.add_metric(f"timeout_recovery_{timeout}s", "response_time", elapsed_time)
                print(f"    成功 (耗时: {elapsed_time:.2f}s)")
            except Exception as e:
                elapsed_time = time.time() - start_time
                timeout_tests.append({"timeout": timeout, "success": False, "time": elapsed_time})
                metrics.add_metric(f"timeout_recovery_{timeout}s", "success", 0)
                metrics.add_metric(f"timeout_recovery_{timeout}s", "response_time", elapsed_time)
                print(f"    超时或错误 (耗时: {elapsed_time:.2f}s)")
    
    # 测试故障转移
    print("\n2. 故障转移测试")
    # 测试正常长度的输入，确保故障转移机制正常工作
    for i in range(10):
        try:
            # 使用合理长度的输入
            response = LLM_Wrapper.generate(
                model_name="gpt41_normal",
                prompt=f"Test failover {i}: " + "This is a test prompt. " * 50,  # 约250个单词
                mode="fast_first",
                timeout=20
            )
            metrics.add_metric("failover_test", "success", 1)
            print(f"  测试 {i+1}: 成功")
        except Exception as e:
            metrics.add_metric("failover_test", "success", 0)
            print(f"  测试 {i+1}: 失败 - {str(e)[:50]}")

def test_multimodal_performance(metrics: PerformanceMetrics):
    """测试多模态性能"""
    print("\n=== 多模态性能测试 ===")
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print("测试图片不存在，跳过多模态测试")
        return
    
    with open(TEST_IMAGE_PATH, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    
    mm_models = ["gpt41_normal_mm", "llama4_maverick_mm", "gemini25_flash_mm"]
    prompts = [
        "Describe this image",
        "What colors do you see?",
        "Count the objects",
        "Is this indoor or outdoor?",
        "What's the main subject?"
    ]
    
    for model in mm_models:
        print(f"\n测试多模态模型: {model}")
        mm_times = []
        
        for i in range(10):
            prompt = prompts[i % len(prompts)]
            try:
                start_time = time.time()
                response = LLM_Wrapper.generate_mm(
                    model_name=model,
                    prompt=prompt,
                    img_base64=img_base64,
                    mode="fast_first",
                    timeout=30
                )
                elapsed_time = time.time() - start_time
                mm_times.append(elapsed_time)
                metrics.add_metric(f"multimodal_{model}", "response_time", elapsed_time)
                metrics.add_metric(f"multimodal_{model}", "success", 1)
            except Exception as e:
                metrics.add_metric(f"multimodal_{model}", "success", 0)
                print(f"  错误: {str(e)[:50]}")
        
        if mm_times:
            print(f"  平均响应时间: {statistics.mean(mm_times):.2f}s")

def test_cost_optimization(metrics: PerformanceMetrics):
    """测试成本优化模式"""
    print("\n=== 成本优化测试 ===")
    
    models = ["gpt41_normal", "gemini20_flash", "llama4_maverick", "claude37_normal"]
    
    # 测试 cheap_first 模式
    print("\n1. Cheap First 模式")
    cheap_times = []
    
    for i in range(20):
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate_fromTHEbest(
                model_list=models,
                prompt=f"Simple test {i}",
                mode="cheap_first",
                timeout=30
            )
            elapsed_time = time.time() - start_time
            cheap_times.append(elapsed_time)
            metrics.add_metric("cost_optimization_cheap", "response_time", elapsed_time)
            metrics.add_metric("cost_optimization_cheap", "success", 1)
        except Exception as e:
            metrics.add_metric("cost_optimization_cheap", "success", 0)
    
    # 测试 fast_first 模式
    print("\n2. Fast First 模式")
    fast_times = []
    
    for i in range(20):
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate_fromTHEbest(
                model_list=models,
                prompt=f"Simple test {i}",
                mode="fast_first",
                timeout=30
            )
            elapsed_time = time.time() - start_time
            fast_times.append(elapsed_time)
            metrics.add_metric("cost_optimization_fast", "response_time", elapsed_time)
            metrics.add_metric("cost_optimization_fast", "success", 1)
        except Exception as e:
            metrics.add_metric("cost_optimization_fast", "success", 0)
    
    if cheap_times and fast_times:
        print(f"\nCheap First 平均时间: {statistics.mean(cheap_times):.2f}s")
        print(f"Fast First 平均时间: {statistics.mean(fast_times):.2f}s")
        print(f"时间差异: {abs(statistics.mean(cheap_times) - statistics.mean(fast_times)):.2f}s")

# ==================== 主测试函数 ====================

def run_performance_tests():
    """运行所有性能测试"""
    metrics = PerformanceMetrics()
    
    print("="*60)
    print("开始性能测试套件")
    print("="*60)
    
    # 基础性能测试
    test_response_time_distribution(metrics, num_samples=30)
    
    # 并发性能测试
    test_concurrent_load(metrics, num_workers=5, duration=30)
    
    # 切换开销测试
    test_model_switching_overhead(metrics)
    
    # 错误恢复测试
    test_error_recovery(metrics)
    
    # 多模态性能测试
    test_multimodal_performance(metrics)
    
    # 成本优化测试
    test_cost_optimization(metrics)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics.save(f"performance_test_results_{timestamp}.json")
    metrics.plot_results(f"performance_test_charts_{timestamp}.png")
    
    # 打印总结
    print("\n" + "="*60)
    print("性能测试总结")
    print("="*60)
    
    metrics.calculate_summary()
    for test_name, summary in metrics.metrics["summary"].items():
        print(f"\n{test_name}:")
        for metric_name, stats in summary.items():
            if isinstance(stats, dict) and "mean" in stats:
                print(f"  {metric_name}: 平均={stats['mean']:.2f}, P95={stats['p95']:.2f}, 最大={stats['max']:.2f}")

def run_stress_test():
    """运行压力测试"""
    metrics = PerformanceMetrics()
    
    print("="*60)
    print("开始压力测试")
    print("="*60)
    
    # 高并发压力测试
    print("\n高并发压力测试...")
    test_concurrent_load(metrics, num_workers=20, duration=120)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics.save(f"stress_test_results_{timestamp}.json")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "stress":
            run_stress_test()
        elif sys.argv[1] == "quick":
            # 快速性能测试
            metrics = PerformanceMetrics()
            test_response_time_distribution(metrics, num_samples=10)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics.save(f"quick_performance_test_{timestamp}.json")
    else:
        run_performance_tests() 