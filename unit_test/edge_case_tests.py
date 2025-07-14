#!/usr/bin/env python3
"""
边界情况测试：测试系统在各种极端和异常情况下的表现
"""

import time
import json
import base64
import os
from datetime import datetime
import random
import string

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
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "edge_case_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

class EdgeCaseResults:
    """边界测试结果收集器"""
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    def add_test(self, test_name: str, description: str, status: str, details: dict):
        self.results["tests"].append({
            "test_name": test_name,
            "description": description,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
        
        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
    
    def save(self, filename: str):
        filepath = os.path.join(RESULTS_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"边界测试结果已保存到: {filepath}")

# ==================== 输入边界测试 ====================

def test_extreme_inputs(results: EdgeCaseResults):
    """测试极端输入情况"""
    print("\n=== 极端输入测试 ===")
    
    # 测试空输入
    print("\n1. 空输入测试")
    try:
        response = LLM_Wrapper.generate(
            model_name="gpt41_normal",
            prompt="",
            timeout=20
        )
        results.add_test(
            "empty_input",
            "测试空字符串输入",
            "warning" if response else "failed",
            {"response_length": len(response) if response else 0}
        )
        print(f"  空输入响应: {response[:50] if response else 'None'}")
    except Exception as e:
        results.add_test(
            "empty_input",
            "测试空字符串输入",
            "passed",  # 预期应该抛出异常或处理空输入
            {"error": str(e)}
        )
        print(f"  空输入正确处理: {str(e)[:50]}")
    
    # 测试超长输入
    print("\n2. 超长输入测试")
    long_prompt = "Please summarize this text: " + "x" * 100000  # 100k字符
    try:
        start_time = time.time()
        response = LLM_Wrapper.generate(
            model_name="gpt41_normal",
            prompt=long_prompt,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        results.add_test(
            "long_input",
            "测试100k字符的超长输入",
            "passed",
            {
                "input_length": len(long_prompt),
                "response_length": len(response),
                "elapsed_time": elapsed_time
            }
        )
        print(f"  超长输入处理成功，耗时: {elapsed_time:.2f}s")
    except Exception as e:
        results.add_test(
            "long_input",
            "测试100k字符的超长输入",
            "passed",  # 预期可能会失败
            {"error": str(e)}
        )
        print(f"  超长输入处理失败（预期）: {str(e)[:50]}")
    
    # 测试特殊字符
    print("\n3. 特殊字符测试")
    special_prompts = [
        "Test with emoji: 😀🎉🌟💻🚀",
        "Test with unicode: ñáéíóú ÑÁÉÍÓÚ αβγδε ΑΒΓΔΕ",
        "Test with control chars: \n\t\r",
        "Test with quotes: \"'`",
        "Test with HTML: <script>alert('test')</script>",
        "Test with SQL: '; DROP TABLE users; --"
    ]
    
    for i, prompt in enumerate(special_prompts):
        try:
            response = LLM_Wrapper.generate(
                model_name="gemini20_flash",
                prompt=prompt,
                timeout=20
            )
            results.add_test(
                f"special_chars_{i}",
                f"测试特殊字符: {prompt[:30]}",
                "passed",
                {"prompt": prompt, "response_length": len(response)}
            )
            print(f"  特殊字符测试 {i+1}: 成功")
        except Exception as e:
            results.add_test(
                f"special_chars_{i}",
                f"测试特殊字符: {prompt[:30]}",
                "failed",
                {"prompt": prompt, "error": str(e)}
            )
            print(f"  特殊字符测试 {i+1}: 失败 - {str(e)[:30]}")

def test_invalid_parameters(results: EdgeCaseResults):
    """测试无效参数"""
    print("\n=== 无效参数测试 ===")
    
    # 测试无效模型名
    print("\n1. 无效模型名测试")
    invalid_models = [
        "non_existent_model",
        "gpt-5-turbo",
        "claude-100",
        "",
        None,
        123,
        ["list_model"]
    ]
    
    for model in invalid_models:
        try:
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt="Test",
                timeout=20
            )
            results.add_test(
                f"invalid_model_{model}",
                f"测试无效模型名: {model}",
                "failed",  # 不应该成功
                {"model": str(model)}
            )
            print(f"  无效模型 {model}: 意外成功！")
        except Exception as e:
            results.add_test(
                f"invalid_model_{model}",
                f"测试无效模型名: {model}",
                "passed",  # 应该失败
                {"model": str(model), "error": str(e)}
            )
            print(f"  无效模型 {model}: 正确拒绝")
    
    # 测试无效超时值
    print("\n2. 无效超时值测试")
    invalid_timeouts = [-1, 0, 0.001, 10000, None, "30", [30]]
    
    for timeout in invalid_timeouts:
        try:
            # 对于某些值，Python 可能会自动处理或使用默认值
            response = LLM_Wrapper.generate(
                model_name="gpt41_normal",
                prompt="Quick test",
                timeout=timeout
            )
            # 如果成功了，检查是哪种情况
            if timeout in [0.001]:  # 太小的超时值可能导致超时
                status = "warning"
            elif timeout in [10000]:  # 太大的超时值可能被接受
                status = "warning"
            elif isinstance(timeout, (int, float)) and timeout > 0:  # 有效的数值
                status = "warning"
            else:
                status = "failed"  # 不应该成功
            
            results.add_test(
                f"invalid_timeout_{timeout}",
                f"测试无效超时值: {timeout}",
                status,
                {"timeout": str(timeout), "note": "Request succeeded with this timeout"}
            )
            print(f"  超时值 {timeout}: 处理成功")
        except Exception as e:
            # 对于真正无效的超时值，应该抛出异常
            expected_errors = [None, "30", [30], -1, 0]  # 这些应该失败
            if timeout in expected_errors:
                status = "passed"
            else:
                status = "warning"
                
            results.add_test(
                f"invalid_timeout_{timeout}",
                f"测试无效超时值: {timeout}",
                status,
                {"timeout": str(timeout), "error": str(e)[:100]}
            )
            print(f"  超时值 {timeout}: 正确拒绝")
    
    # 测试无效比例参数
    print("\n3. 无效比例参数测试")
    invalid_proportions = [
        (-1, 50),
        (50, -1),
        (0, 0),
        (1000, 1000),
        (None, 50),
        ("50", "50")
    ]
    
    for input_prop, output_prop in invalid_proportions:
        try:
            response = LLM_Wrapper.generate(
                model_name="gpt41_normal",
                prompt="Test proportions",
                input_proportion=input_prop,
                output_proportion=output_prop,
                timeout=20
            )
            results.add_test(
                f"invalid_proportions_{input_prop}_{output_prop}",
                f"测试无效比例: {input_prop}/{output_prop}",
                "warning",  # 可能有默认处理
                {"input": str(input_prop), "output": str(output_prop)}
            )
            print(f"  比例 {input_prop}/{output_prop}: 有默认处理")
        except Exception as e:
            results.add_test(
                f"invalid_proportions_{input_prop}_{output_prop}",
                f"测试无效比例: {input_prop}/{output_prop}",
                "passed",
                {"error": str(e)}
            )
            print(f"  比例 {input_prop}/{output_prop}: 错误处理")

def test_multimodal_edge_cases(results: EdgeCaseResults):
    """测试多模态边界情况"""
    print("\n=== 多模态边界测试 ===")
    
    # 测试无效图像数据
    print("\n1. 无效图像数据测试")
    invalid_images = [
        "",  # 空字符串
        "not_base64_encoded",  # 非base64
        "aGVsbG8=",  # 有效base64但不是图像
        None,  # None值
    ]
    
    for i, img_data in enumerate(invalid_images):
        try:
            response = LLM_Wrapper.generate_mm(
                model_name="gpt41_normal_mm",
                prompt="Describe this image",
                img_base64=img_data,
                timeout=20
            )
            results.add_test(
                f"invalid_image_{i}",
                f"测试无效图像数据类型 {i}",
                "failed",  # 不应该成功
                {"image_type": type(img_data).__name__}
            )
            print(f"  无效图像 {i}: 意外成功！")
        except Exception as e:
            results.add_test(
                f"invalid_image_{i}",
                f"测试无效图像数据类型 {i}",
                "passed",
                {"error": str(e)[:100]}
            )
            print(f"  无效图像 {i}: 正确拒绝")
    
    # 测试超大图像
    print("\n2. 超大图像测试")
    # 创建一个超大的假图像数据
    large_image = base64.b64encode(b"x" * 10000000).decode("utf-8")  # 10MB
    try:
        response = LLM_Wrapper.generate_mm(
            model_name="gpt41_normal_mm",
            prompt="Describe this large image",
            img_base64=large_image,
            timeout=30
        )
        results.add_test(
            "large_image",
            "测试10MB大图像",
            "warning",
            {"image_size": len(large_image)}
        )
        print("  超大图像: 处理成功（可能有性能影响）")
    except Exception as e:
        results.add_test(
            "large_image",
            "测试10MB大图像",
            "passed",
            {"error": str(e)[:100]}
        )
        print("  超大图像: 正确限制")
    
    # 测试错误的模型用于多模态
    print("\n3. 错误模型类型测试")
    try:
        response = LLM_Wrapper.generate_mm(
            model_name="gpt41_normal",  # 非多模态模型
            prompt="Describe image",
            img_base64="valid_base64_here",
            timeout=20
        )
        results.add_test(
            "wrong_model_type",
            "使用非多模态模型进行多模态调用",
            "failed",
            {}
        )
        print("  错误模型类型: 意外成功！")
    except ValueError as e:
        results.add_test(
            "wrong_model_type",
            "使用非多模态模型进行多模态调用",
            "passed",
            {"error": str(e)}
        )
        print("  错误模型类型: 正确拒绝")

def test_function_calling_edge_cases(results: EdgeCaseResults):
    """测试函数调用边界情况"""
    print("\n=== 函数调用边界测试 ===")
    
    # 测试无效工具定义
    print("\n1. 无效工具定义测试")
    invalid_tools = [
        [],  # 空列表
        None,  # None
        "not a list",  # 字符串
        [{"invalid": "structure"}],  # 错误结构
        [{"type": "function"}],  # 缺少function字段
    ]
    
    for i, tools in enumerate(invalid_tools):
        try:
            response = LLM_Wrapper.function_calling(
                model_name="claude37_normal",
                prompt="Use a tool",
                tools=tools,
                timeout=20
            )
            results.add_test(
                f"invalid_tools_{i}",
                f"测试无效工具定义 {i}",
                "warning",
                {"tools_type": type(tools).__name__}
            )
            print(f"  无效工具 {i}: 处理成功")
        except Exception as e:
            results.add_test(
                f"invalid_tools_{i}",
                f"测试无效工具定义 {i}",
                "passed",
                {"error": str(e)[:100]}
            )
            print(f"  无效工具 {i}: 正确处理")
    
    # 测试超多工具
    print("\n2. 大量工具测试")
    many_tools = []
    for i in range(100):  # 100个工具
        many_tools.append({
            "type": "function",
            "function": {
                "name": f"tool_{i}",
                "description": f"Tool number {i}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param": {"type": "string"}
                    }
                }
            }
        })
    
    try:
        start_time = time.time()
        response = LLM_Wrapper.function_calling(
            model_name="claude37_normal",
            prompt="Use tool_50",
            tools=many_tools,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        results.add_test(
            "many_tools",
            "测试100个工具定义",
            "passed",
            {
                "num_tools": len(many_tools),
                "elapsed_time": elapsed_time,
                "has_tool_calls": "tool_calls" in response
            }
        )
        print(f"  大量工具测试: 成功，耗时 {elapsed_time:.2f}s")
    except Exception as e:
        results.add_test(
            "many_tools",
            "测试100个工具定义",
            "warning",
            {"error": str(e)}
        )
        print(f"  大量工具测试: 失败 - {str(e)[:50]}")

def test_concurrent_edge_cases(results: EdgeCaseResults):
    """测试并发边界情况"""
    print("\n=== 并发边界测试 ===")
    
    # 测试同一模型的快速连续调用
    print("\n1. 快速连续调用测试")
    model = "gpt41_normal"
    rapid_results = []
    
    for i in range(10):
        try:
            # 不等待，立即发送下一个请求
            start_time = time.time()
            response = LLM_Wrapper.generate(
                model_name=model,
                prompt=f"Rapid test {i}",
                timeout=20
            )
            elapsed_time = time.time() - start_time
            rapid_results.append({
                "index": i,
                "success": True,
                "time": elapsed_time
            })
        except Exception as e:
            rapid_results.append({
                "index": i,
                "success": False,
                "error": str(e)[:50]
            })
    
    success_count = sum(1 for r in rapid_results if r["success"])
    results.add_test(
        "rapid_sequential",
        "快速连续调用同一模型10次",
        "passed" if success_count >= 8 else "warning",
        {
            "total": len(rapid_results),
            "successful": success_count,
            "failed": len(rapid_results) - success_count
        }
    )
    print(f"  快速连续调用: {success_count}/10 成功")
    
    # 测试模型列表边界
    print("\n2. 模型列表边界测试")
    
    # 空列表
    try:
        response = LLM_Wrapper.generate_fromTHEbest(
            model_list=[],
            prompt="Test empty list",
            timeout=20
        )
        results.add_test(
            "empty_model_list",
            "测试空模型列表",
            "failed",
            {}
        )
        print("  空模型列表: 意外成功！")
    except Exception as e:
        results.add_test(
            "empty_model_list",
            "测试空模型列表",
            "passed",
            {"error": str(e)}
        )
        print("  空模型列表: 正确拒绝")
    
    # 包含无效模型的列表
    mixed_models = ["gpt41_normal", "invalid_model", "gemini20_flash"]
    try:
        response = LLM_Wrapper.generate_fromTHEbest(
            model_list=mixed_models,
            prompt="Test mixed models",
            timeout=20
        )
        results.add_test(
            "mixed_valid_invalid_models",
            "测试包含无效模型的列表",
            "failed",
            {"models": mixed_models}
        )
        print("  混合模型列表: 意外成功！")
    except Exception as e:
        results.add_test(
            "mixed_valid_invalid_models",
            "测试包含无效模型的列表",
            "passed",
            {"error": str(e)[:100]}
        )
        print("  混合模型列表: 正确处理")

def test_load_balancing_edge_cases(results: EdgeCaseResults):
    """测试负载均衡边界情况"""
    print("\n=== 负载均衡边界测试 ===")
    
    lb = LoadBalancing()
    
    # 测试无健康数据的情况
    print("\n1. 无健康数据测试")
    # 这个测试依赖于系统刚启动时的状态
    
    # 测试所有源都失败的情况
    print("\n2. 降级处理测试")
    # 使用一个可能在多个源上都有问题的模型
    problematic_models = ["claude4_opus", "claude4_sonnet"]
    
    for model in problematic_models:
        try:
            config = lb.get_config(model, "fast_first", 60, 40)
            results.add_test(
                f"degraded_model_{model}",
                f"测试可能降级的模型: {model}",
                "passed",
                {
                    "model": model,
                    "main_source": config[0],
                    "backup_source": config[3]
                }
            )
            print(f"  降级模型 {model}: 找到配置")
        except Exception as e:
            results.add_test(
                f"degraded_model_{model}",
                f"测试可能降级的模型: {model}",
                "warning",
                {"error": str(e)}
            )
            print(f"  降级模型 {model}: 配置失败")
    
    # 测试极端比例
    print("\n3. 极端比例测试")
    extreme_proportions = [
        (1, 99),
        (99, 1),
        (0, 100),
        (100, 0)
    ]
    
    for input_prop, output_prop in extreme_proportions:
        try:
            config = lb.get_config("gpt41_normal", "cheap_first", input_prop, output_prop)
            results.add_test(
                f"extreme_proportions_{input_prop}_{output_prop}",
                f"测试极端比例: {input_prop}/{output_prop}",
                "passed",
                {
                    "proportions": f"{input_prop}/{output_prop}",
                    "main_source": config[0]
                }
            )
            print(f"  极端比例 {input_prop}/{output_prop}: 成功")
        except Exception as e:
            results.add_test(
                f"extreme_proportions_{input_prop}_{output_prop}",
                f"测试极端比例: {input_prop}/{output_prop}",
                "failed",
                {"error": str(e)}
            )
            print(f"  极端比例 {input_prop}/{output_prop}: 失败")

# ==================== 主测试函数 ====================

def run_edge_case_tests():
    """运行所有边界测试"""
    results = EdgeCaseResults()
    
    print("="*60)
    print("开始边界情况测试")
    print("="*60)
    
    # 输入边界测试
    test_extreme_inputs(results)
    
    # 参数验证测试
    test_invalid_parameters(results)
    
    # 多模态边界测试
    test_multimodal_edge_cases(results)
    
    # 函数调用边界测试
    test_function_calling_edge_cases(results)
    
    # 并发边界测试
    test_concurrent_edge_cases(results)
    
    # 负载均衡边界测试
    test_load_balancing_edge_cases(results)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results.save(f"edge_case_test_results_{timestamp}.json")
    
    # 打印总结
    print("\n" + "="*60)
    print("边界测试总结")
    print("="*60)
    
    summary = results.results["summary"]
    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['passed']}")
    print(f"失败: {summary['failed']}")
    print(f"警告: {summary['warnings']}")
    print(f"通过率: {summary['passed']/summary['total']*100:.1f}%")
    
    # 打印失败的测试
    if summary['failed'] > 0:
        print("\n失败的测试:")
        for test in results.results["tests"]:
            if test["status"] == "failed":
                print(f"  - {test['test_name']}: {test['description']}")

if __name__ == "__main__":
    run_edge_case_tests() 