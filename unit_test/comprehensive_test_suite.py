#!/usr/bin/env python3
"""
全面测试套件：包含单元测试、集成测试和压力测试
测试所有模块的功能和性能
"""

import time
import json
import base64
import os
import concurrent.futures
import statistics
from datetime import datetime
from typing import List, Dict, Tuple
import random

from LLMwrapper import LLM_Wrapper
from LoadBalancing import LoadBalancing
from ew_config.source import (
    model_list_normal, 
    model_list_thinking, 
    model_list_mm_normal, 
    model_list_mm_thinking,
    model_list_function_calling
)

# 测试配置
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test.jpg")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "test_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

class TestResults:
    """测试结果收集器"""
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
    
    def add_test(self, test_name: str, status: str, details: dict):
        self.results["tests"].append({
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
    
    def save(self, filename: str):
        filepath = os.path.join(RESULTS_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"测试结果已保存到: {filepath}")

# ==================== 单元测试 ====================

def test_text_generation_models(results: TestResults):
    """测试所有文本生成模型"""
    print("\n=== 测试文本生成模型 ===")
    
    test_prompts = [
        "What is 2+2?",
        "Write a haiku about spring",
        "Explain quantum computing in one sentence",
        "List 3 benefits of exercise"
    ]
    
    # 测试普通模型
    for model in model_list_normal[:5]:  # 测试前5个模型
        print(f"\n测试模型: {model}")
        for prompt in test_prompts[:2]:  # 每个模型测试2个提示
            try:
                start_time = time.time()
                response = LLM_Wrapper.generate(
                    model_name=model,
                    prompt=prompt,
                    mode="fast_first",
                    timeout=30
                )
                elapsed_time = time.time() - start_time
                
                results.add_test(
                    f"text_generation_{model}",
                    "success",
                    {
                        "model": model,
                        "prompt": prompt,
                        "response_length": len(response),
                        "elapsed_time": elapsed_time,
                        "response_preview": response[:100]
                    }
                )
                print(f"✓ {model} - 响应时间: {elapsed_time:.2f}s")
            except Exception as e:
                results.add_test(
                    f"text_generation_{model}",
                    "failed",
                    {
                        "model": model,
                        "prompt": prompt,
                        "error": str(e)
                    }
                )
                print(f"✗ {model} - 错误: {str(e)[:100]}")

def test_thinking_models(results: TestResults):
    """测试推理模型"""
    print("\n=== 测试推理模型 ===")
    
    thinking_prompts = [
        "Solve step by step: If a train travels 120 km in 2 hours, what is its speed in m/s?",
        "Analyze the logical fallacy in: All birds can fly. Penguins are birds. Therefore, penguins can fly."
    ]
    
    for model in model_list_thinking[:3]:  # 测试前3个推理模型
        print(f"\n测试推理模型: {model}")
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=thinking_prompts[0],
                mode="fast_first",
                timeout=60  # 推理模型需要更长时间
            )
            elapsed_time = time.time() - start_time
            
            results.add_test(
                f"thinking_model_{model}",
                "success",
                {
                    "model": model,
                    "elapsed_time": elapsed_time,
                    "response_length": len(response)
                }
            )
            print(f"✓ {model} - 响应时间: {elapsed_time:.2f}s")
        except Exception as e:
            results.add_test(
                f"thinking_model_{model}",
                "failed",
                {"model": model, "error": str(e)}
            )
            print(f"✗ {model} - 错误: {str(e)[:100]}")

def test_multimodal_models(results: TestResults):
    """测试多模态模型"""
    print("\n=== 测试多模态模型 ===")
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"测试图片不存在: {TEST_IMAGE_PATH}")
        return
    
    with open(TEST_IMAGE_PATH, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    
    mm_prompts = [
        "Describe this image in detail",
        "What color is the main object in this image?",
        "Count the objects in this image"
    ]
    
    for model in model_list_mm_normal[:4]:  # 测试前4个多模态模型
        print(f"\n测试多模态模型: {model}")
        for prompt in mm_prompts[:2]:
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
                
                results.add_test(
                    f"multimodal_{model}",
                    "success",
                    {
                        "model": model,
                        "prompt": prompt,
                        "elapsed_time": elapsed_time,
                        "response_preview": response[:100]
                    }
                )
                print(f"✓ {model} - 响应时间: {elapsed_time:.2f}s")
            except Exception as e:
                results.add_test(
                    f"multimodal_{model}",
                    "failed",
                    {"model": model, "prompt": prompt, "error": str(e)}
                )
                print(f"✗ {model} - 错误: {str(e)[:100]}")

def test_function_calling(results: TestResults):
    """测试函数调用功能"""
    print("\n=== 测试函数调用 ===")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    test_queries = [
        "Calculate 15 * 23 + 47",
        "Search for the latest news about AI"
    ]
    
    for model in model_list_function_calling[:3]:
        print(f"\n测试函数调用模型: {model}")
        try:
            start_time = time.time()
            response = LLM_Wrapper.function_calling(
                model_name=model,
                prompt=test_queries[0],
                tools=tools,
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            has_tool_calls = "tool_calls" in response and response["tool_calls"]
            
            # 序列化 tool_calls 以便保存到 JSON
            serialized_tool_calls = []
            if has_tool_calls:
                for tool_call in response["tool_calls"]:
                    if hasattr(tool_call, "__dict__"):
                        # 如果是对象，转换为字典
                        serialized_call = {
                            "id": getattr(tool_call, "id", ""),
                            "type": getattr(tool_call, "type", "function"),
                            "function": {
                                "name": getattr(getattr(tool_call, "function", {}), "name", ""),
                                "arguments": getattr(getattr(tool_call, "function", {}), "arguments", "{}")
                            }
                        }
                        serialized_tool_calls.append(serialized_call)
                    elif isinstance(tool_call, dict):
                        serialized_tool_calls.append(tool_call)
            
            results.add_test(
                f"function_calling_{model}",
                "success",
                {
                    "model": model,
                    "elapsed_time": elapsed_time,
                    "has_tool_calls": has_tool_calls,
                    "tool_calls": len(serialized_tool_calls),
                    "tool_calls_detail": serialized_tool_calls[:1] if serialized_tool_calls else []  # 只保存第一个作为示例
                }
            )
            print(f"✓ {model} - 工具调用: {has_tool_calls}")
        except Exception as e:
            results.add_test(
                f"function_calling_{model}",
                "failed",
                {"model": model, "error": str(e)}
            )
            print(f"✗ {model} - 错误: {str(e)[:100]}")

# ==================== 集成测试 ====================

def test_pareto_optimal_selection(results: TestResults):
    """测试帕累托最优选择"""
    print("\n=== 测试帕累托最优选择 ===")
    
    # 测试文本模型选择
    text_models = ["gpt41_normal", "gemini20_flash", "llama4_maverick", "claude37_normal"]
    print(f"\n测试文本模型批量选择: {text_models}")
    
    try:
        start_time = time.time()
        response = LLM_Wrapper.generate_fromTHEbest(
            model_list=text_models,
            prompt="Explain the concept of machine learning in 50 words",
            mode="fast_first",
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        results.add_test(
            "pareto_text_selection",
            "success",
            {
                "models": text_models,
                "mode": "fast_first",
                "elapsed_time": elapsed_time,
                "response_length": len(response)
            }
        )
        print(f"✓ 文本模型选择成功 - 时间: {elapsed_time:.2f}s")
    except Exception as e:
        results.add_test(
            "pareto_text_selection",
            "failed",
            {"models": text_models, "error": str(e)}
        )
        print(f"✗ 文本模型选择失败: {str(e)[:100]}")
    
    # 测试多模态模型选择
    if os.path.exists(TEST_IMAGE_PATH):
        with open(TEST_IMAGE_PATH, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        
        mm_models = ["gpt41_normal_mm", "llama4_maverick_mm", "gemini25_flash_mm"]
        print(f"\n测试多模态模型批量选择: {mm_models}")
        
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate_mm_fromTHEbest(
                model_list=mm_models,
                prompt="What objects do you see?",
                img_base64=img_base64,
                mode="cheap_first",
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            results.add_test(
                "pareto_mm_selection",
                "success",
                {
                    "models": mm_models,
                    "mode": "cheap_first",
                    "elapsed_time": elapsed_time
                }
            )
            print(f"✓ 多模态模型选择成功 - 时间: {elapsed_time:.2f}s")
        except Exception as e:
            results.add_test(
                "pareto_mm_selection",
                "failed",
                {"models": mm_models, "error": str(e)}
            )
            print(f"✗ 多模态模型选择失败: {str(e)[:100]}")

def test_load_balancing_failover(results: TestResults):
    """测试负载均衡故障转移"""
    print("\n=== 测试负载均衡故障转移 ===")
    
    lb = LoadBalancing()
    
    # 测试获取配置
    test_models = ["gpt41_normal", "gpt41_normal_mm", "claude37_normal"]
    
    for model in test_models:
        try:
            config = lb.get_config(model, "fast_first", 60, 40)
            results.add_test(
                f"load_balancing_{model}",
                "success",
                {
                    "model": model,
                    "main_source": config[0],
                    "backup_source": config[3],
                    "main_model": config[1],
                    "backup_model": config[4]
                }
            )
            print(f"✓ {model} - 主源: {config[0]}, 备源: {config[3]}")
        except Exception as e:
            results.add_test(
                f"load_balancing_{model}",
                "failed",
                {"model": model, "error": str(e)}
            )
            print(f"✗ {model} - 错误: {str(e)[:100]}")

# ==================== 压力测试 ====================

def stress_test_concurrent_requests(results: TestResults, num_requests: int = 10):
    """并发请求压力测试"""
    print(f"\n=== 并发压力测试 ({num_requests} 个请求) ===")
    
    def make_request(index: int) -> Tuple[int, float, bool, str]:
        """执行单个请求"""
        models = ["gpt41_normal", "gemini20_flash", "llama4_maverick"]
        model = models[index % len(models)]
        prompts = [
            "What is the capital of France?",
            "Explain AI in one sentence",
            "List 3 programming languages"
        ]
        prompt = prompts[index % len(prompts)]
        
        try:
            start_time = time.time()
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=prompt,
                mode="fast_first",
                timeout=30
            )
            elapsed_time = time.time() - start_time
            return index, elapsed_time, True, model
        except Exception as e:
            elapsed_time = time.time() - start_time
            return index, elapsed_time, False, f"{model}: {str(e)[:50]}"
    
    # 执行并发请求
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        results_list = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    
    # 统计结果
    successful = [r for r in results_list if r[2]]
    failed = [r for r in results_list if not r[2]]
    response_times = [r[1] for r in successful]
    
    stats = {
        "total_requests": num_requests,
        "successful": len(successful),
        "failed": len(failed),
        "total_time": total_time,
        "avg_response_time": statistics.mean(response_times) if response_times else 0,
        "min_response_time": min(response_times) if response_times else 0,
        "max_response_time": max(response_times) if response_times else 0,
        "requests_per_second": num_requests / total_time
    }
    
    results.add_test(
        "stress_test_concurrent",
        "completed",
        stats
    )
    
    print(f"完成: {stats['successful']}/{num_requests} 成功")
    print(f"平均响应时间: {stats['avg_response_time']:.2f}s")
    print(f"请求速率: {stats['requests_per_second']:.2f} req/s")

def stress_test_sustained_load(results: TestResults, duration_seconds: int = 60):
    """持续负载压力测试"""
    print(f"\n=== 持续负载测试 ({duration_seconds}秒) ===")
    
    models = ["gpt41_normal", "gemini20_flash", "llama4_maverick"]
    request_count = 0
    success_count = 0
    error_count = 0
    response_times = []
    
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    while time.time() < end_time:
        model = random.choice(models)
        prompt = f"Generate a random number between 1 and 100. Current time: {time.time()}"
        
        try:
            req_start = time.time()
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=prompt,
                mode="fast_first",
                timeout=20
            )
            req_time = time.time() - req_start
            response_times.append(req_time)
            success_count += 1
        except Exception as e:
            error_count += 1
        
        request_count += 1
        
        # 每10个请求打印一次状态
        if request_count % 10 == 0:
            elapsed = time.time() - start_time
            print(f"进度: {elapsed:.0f}s, 请求: {request_count}, 成功: {success_count}, 失败: {error_count}")
        
        # 控制请求速率，避免过载
        time.sleep(0.5)
    
    total_duration = time.time() - start_time
    
    stats = {
        "duration": total_duration,
        "total_requests": request_count,
        "successful": success_count,
        "failed": error_count,
        "success_rate": success_count / request_count if request_count > 0 else 0,
        "avg_response_time": statistics.mean(response_times) if response_times else 0,
        "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else (max(response_times) if response_times else 0),
        "requests_per_second": request_count / total_duration
    }
    
    results.add_test(
        "stress_test_sustained",
        "completed",
        stats
    )
    
    print(f"\n持续负载测试完成:")
    print(f"成功率: {stats['success_rate']*100:.1f}%")
    print(f"平均响应时间: {stats['avg_response_time']:.2f}s")
    print(f"P95响应时间: {stats['p95_response_time']:.2f}s")

def stress_test_model_switching(results: TestResults):
    """测试模型切换性能"""
    print("\n=== 模型切换压力测试 ===")
    
    model_groups = [
        ["gpt41_normal", "gemini20_flash", "llama4_maverick"],
        ["claude37_normal", "gpt41_normal"],
        ["gemini25_flash", "llama4_scout"]
    ]
    
    switch_times = []
    
    for i in range(5):  # 5轮测试
        for models in model_groups:
            try:
                start_time = time.time()
                response = LLM_Wrapper.generate_fromTHEbest(
                    model_list=models,
                    prompt=f"Test prompt {i}",
                    mode="fast_first",
                    timeout=30
                )
                switch_time = time.time() - start_time
                switch_times.append(switch_time)
                print(f"✓ 轮次 {i+1} - 模型组 {models[0]}... - 时间: {switch_time:.2f}s")
            except Exception as e:
                print(f"✗ 轮次 {i+1} - 错误: {str(e)[:50]}")
    
    if switch_times:
        stats = {
            "total_switches": len(switch_times),
            "avg_switch_time": statistics.mean(switch_times),
            "min_switch_time": min(switch_times),
            "max_switch_time": max(switch_times)
        }
        results.add_test(
            "stress_test_switching",
            "completed",
            stats
        )
        print(f"\n平均切换时间: {stats['avg_switch_time']:.2f}s")

# ==================== 端到端测试 ====================

def end_to_end_test_scenario(results: TestResults):
    """端到端场景测试"""
    print("\n=== 端到端场景测试 ===")
    
    # 场景1: 多轮对话
    print("\n场景1: 多轮对话测试")
    conversation_history = []
    model = "claude37_normal"
    
    questions = [
        "What is machine learning?",
        "Can you give me a simple example?",
        "How is it different from traditional programming?"
    ]
    
    for i, question in enumerate(questions):
        try:
            # 构建包含历史的提示
            full_prompt = "\n".join(conversation_history + [f"User: {question}", "Assistant:"])
            
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=full_prompt,
                mode="fast_first",
                timeout=30
            )
            
            conversation_history.append(f"User: {question}")
            conversation_history.append(f"Assistant: {response}")
            
            results.add_test(
                f"e2e_conversation_turn_{i+1}",
                "success",
                {
                    "turn": i+1,
                    "question": question,
                    "response_length": len(response)
                }
            )
            print(f"✓ 对话轮次 {i+1} 完成")
        except Exception as e:
            results.add_test(
                f"e2e_conversation_turn_{i+1}",
                "failed",
                {"turn": i+1, "error": str(e)}
            )
            print(f"✗ 对话轮次 {i+1} 失败: {str(e)[:50]}")
    
    # 场景2: 混合模态工作流
    print("\n场景2: 混合模态工作流")
    if os.path.exists(TEST_IMAGE_PATH):
        with open(TEST_IMAGE_PATH, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        
        try:
            # 步骤1: 图像描述
            image_description = LLM_Wrapper.generate_mm(
                model_name="gpt41_normal_mm",
                prompt="Describe this image in detail",
                img_base64=img_base64,
                timeout=30
            )
            
            # 步骤2: 基于描述生成故事
            story = LLM_Wrapper.generate(
                model_name="claude37_normal",
                prompt=f"Based on this description, write a short story: {image_description[:200]}",
                timeout=30
            )
            
            # 步骤3: 提取关键信息
            tools = [{
                "type": "function",
                "function": {
                    "name": "extract_keywords",
                    "description": "Extract keywords from text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of keywords"
                            }
                        },
                        "required": ["keywords"]
                    }
                }
            }]
            
            keyword_result = LLM_Wrapper.function_calling(
                model_name="claude37_normal",
                prompt=f"Extract 5 keywords from this story: {story[:300]}",
                tools=tools,
                timeout=30
            )
            
            results.add_test(
                "e2e_mixed_workflow",
                "success",
                {
                    "image_description_length": len(image_description),
                    "story_length": len(story),
                    "has_function_call": "tool_calls" in keyword_result
                }
            )
            print("✓ 混合模态工作流完成")
        except Exception as e:
            results.add_test(
                "e2e_mixed_workflow",
                "failed",
                {"error": str(e)}
            )
            print(f"✗ 混合模态工作流失败: {str(e)[:100]}")

# ==================== 主测试函数 ====================

def run_all_tests():
    """运行所有测试"""
    results = TestResults()
    
    print("="*60)
    print("开始全面测试套件")
    print("="*60)
    
    # 单元测试
    print("\n【单元测试】")
    test_text_generation_models(results)
    test_thinking_models(results)
    test_multimodal_models(results)
    test_function_calling(results)
    
    # 集成测试
    print("\n【集成测试】")
    test_pareto_optimal_selection(results)
    test_load_balancing_failover(results)
    
    # 端到端测试
    print("\n【端到端测试】")
    end_to_end_test_scenario(results)
    
    # 压力测试
    print("\n【压力测试】")
    stress_test_concurrent_requests(results, num_requests=20)
    stress_test_sustained_load(results, duration_seconds=30)
    stress_test_model_switching(results)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results.save(f"comprehensive_test_results_{timestamp}.json")
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    total_tests = len(results.results["tests"])
    successful = len([t for t in results.results["tests"] if t["status"] in ["success", "completed"]])
    failed = len([t for t in results.results["tests"] if t["status"] == "failed"])
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/total_tests*100:.1f}%")

def run_quick_test():
    """快速测试（用于验证基本功能）"""
    results = TestResults()
    
    print("="*60)
    print("快速功能验证")
    print("="*60)
    
    # 测试一个文本模型
    print("\n测试文本生成...")
    try:
        response = LLM_Wrapper.generate(
            "gpt41_normal",
            "Say hello",
            timeout=20
        )
        print(f"✓ 文本生成成功: {response[:50]}")
    except Exception as e:
        print(f"✗ 文本生成失败: {str(e)[:100]}")
    
    # 测试帕累托选择
    print("\n测试帕累托选择...")
    try:
        response = LLM_Wrapper.generate_fromTHEbest(
            ["gpt41_normal", "gemini20_flash"],
            "What is 1+1?",
            timeout=20
        )
        print(f"✓ 帕累托选择成功: {response[:50]}")
    except Exception as e:
        print(f"✗ 帕累托选择失败: {str(e)[:100]}")
    
    print("\n快速测试完成！")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        run_quick_test()
    else:
        run_all_tests() 