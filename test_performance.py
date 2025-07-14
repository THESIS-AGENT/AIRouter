#!/usr/bin/env python3
"""
API密钥管理器性能测试脚本
用于验证数据库索引和缓存机制的性能提升
"""

import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import statistics
import json

# 测试配置
API_KEY_MANAGER_URL = "http://localhost:8002"
CONCURRENT_REQUESTS = 20
TOTAL_REQUESTS = 100

def get_available_sources():
    """动态获取可用的源列表"""
    try:
        # 尝试从配置中导入
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 从正确的配置文件导入所有配置
        from ew_config.api_keys import pool_mapping
        from ew_config.source import source_mapping
        
        # 获取既在source_mapping中定义又有API密钥的源
        available_sources = [
            source for source in source_mapping.keys() 
            if source in pool_mapping and pool_mapping[source]
        ]
        return available_sources
    except ImportError:
        print("⚠️  无法导入配置，使用默认测试源")
        # 备选方案：通过API尝试
        test_sources = ["openai", "anthropic", "deepinfra", "google", "deerapi", "openrouter", "togetherai"]
        available_sources = []
        
        for source in test_sources:
            try:
                response = requests.post(
                    f"{API_KEY_MANAGER_URL}/get_apikey",
                    json={"source_name": source},
                    timeout=5
                )
                if response.status_code == 200:
                    available_sources.append(source)
                elif response.status_code == 404:
                    continue  # 源不存在
                else:
                    available_sources.append(source)  # 其他错误可能是API密钥问题，但源存在
            except:
                continue
        
        return available_sources

def test_get_api_key(source_name: str, request_id: int):
    """测试获取API密钥的性能"""
    start_time = time.time()
    try:
        response = requests.post(
            f"{API_KEY_MANAGER_URL}/get_apikey",
            json={"source_name": source_name},
            timeout=10
        )
        end_time = time.time()
        
        if response.status_code == 200:
            return {
                "request_id": request_id,
                "source_name": source_name,
                "success": True,
                "response_time": end_time - start_time,
                "api_key_preview": response.json().get("api_key", "")[:8] + "..."
            }
        else:
            return {
                "request_id": request_id,
                "source_name": source_name,
                "success": False,
                "response_time": end_time - start_time,
                "error": f"HTTP {response.status_code}: {response.text[:100]}"
            }
    except Exception as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "source_name": source_name,
            "success": False,
            "response_time": end_time - start_time,
            "error": str(e)
        }

def test_concurrent_performance():
    """测试并发性能"""
    # 动态获取可用源
    test_sources = get_available_sources()
    
    if not test_sources:
        print("❌ 没有找到可用的测试源")
        return
    
    print("🚀 开始API密钥管理器性能测试")
    print(f"📊 配置: {CONCURRENT_REQUESTS}并发, 总共{TOTAL_REQUESTS}次请求")
    print(f"🎯 可用源: {', '.join(test_sources)}")
    print("-" * 60)
    
    # 生成测试任务
    tasks = []
    for i in range(TOTAL_REQUESTS):
        source_name = test_sources[i % len(test_sources)]
        tasks.append((source_name, i))
    
    # 并发执行
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        future_to_task = {
            executor.submit(test_get_api_key, source_name, request_id): (source_name, request_id)
            for source_name, request_id in tasks
        }
        
        for future in as_completed(future_to_task):
            result = future.result()
            results.append(result)
            
            # 实时显示进度
            if len(results) % 10 == 0:
                print(f"⏳ 已完成: {len(results)}/{TOTAL_REQUESTS}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 分析结果
    analyze_results(results, total_time)

def analyze_results(results: list, total_time: float):
    """分析测试结果"""
    print("\n" + "=" * 60)
    print("📊 性能测试结果分析")
    print("=" * 60)
    
    # 基本统计
    successful_results = [r for r in results if r["success"]]
    failed_results = [r for r in results if not r["success"]]
    
    success_rate = len(successful_results) / len(results) * 100
    
    print(f"📈 总请求数: {len(results)}")
    print(f"✅ 成功请求: {len(successful_results)}")
    print(f"❌ 失败请求: {len(failed_results)}")
    print(f"📊 成功率: {success_rate:.1f}%")
    print(f"⏱️  总耗时: {total_time:.2f}s")
    print(f"🔥 平均QPS: {len(results) / total_time:.2f} requests/sec")
    
    if successful_results:
        response_times = [r["response_time"] for r in successful_results]
        
        print(f"\n📊 响应时间统计 (成功请求):")
        print(f"⚡ 平均响应时间: {statistics.mean(response_times):.3f}s")
        print(f"📏 中位数响应时间: {statistics.median(response_times):.3f}s")
        print(f"🏃 最快响应: {min(response_times):.3f}s")
        print(f"🐌 最慢响应: {max(response_times):.3f}s")
        if len(response_times) > 1:
            print(f"📊 标准差: {statistics.stdev(response_times):.3f}s")
        
        # 按源统计
        source_stats = {}
        for result in successful_results:
            source = result["source_name"]
            if source not in source_stats:
                source_stats[source] = []
            source_stats[source].append(result["response_time"])
        
        print(f"\n📊 按源统计:")
        for source, times in source_stats.items():
            if len(times) > 1:
                print(f"  {source}: 平均 {statistics.mean(times):.3f}s, "
                      f"最快 {min(times):.3f}s, 最慢 {max(times):.3f}s")
            else:
                print(f"  {source}: {times[0]:.3f}s (仅1次请求)")
    
    # 失败分析
    if failed_results:
        print(f"\n❌ 失败请求分析:")
        error_types = {}
        source_errors = {}
        
        for result in failed_results:
            error = result.get("error", "Unknown")
            source = result.get("source_name", "Unknown")
            
            error_types[error] = error_types.get(error, 0) + 1
            if source not in source_errors:
                source_errors[source] = 0
            source_errors[source] += 1
        
        print("  错误类型统计:")
        for error, count in error_types.items():
            print(f"    {error}: {count} 次")
        
        print("  按源统计失败:")
        for source, count in source_errors.items():
            print(f"    {source}: {count} 次失败")

def test_cache_refresh():
    """测试缓存刷新功能"""
    print("\n🔄 测试缓存刷新功能")
    try:
        start_time = time.time()
        response = requests.post(f"{API_KEY_MANAGER_URL}/refresh_cache", timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ 缓存刷新成功，耗时: {end_time - start_time:.2f}s")
            result = response.json()
            print(f"📝 响应: {result.get('message', 'N/A')}")
            print(f"📅 时间戳: {result.get('timestamp', 'N/A')}")
        else:
            print(f"❌ 缓存刷新失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 缓存刷新异常: {str(e)}")

def test_stats_endpoint():
    """测试统计信息端点"""
    print("\n📊 获取统计信息")
    try:
        response = requests.get(f"{API_KEY_MANAGER_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 统计信息获取成功:")
            print(f"📅 最后更新: {stats.get('last_update', 'N/A')}")
            print(f"🔑 失败密钥总数: {stats.get('total_failed_keys', 0)}")
            
            failed_by_source = stats.get('failed_keys_by_source', {})
            if failed_by_source:
                print(f"📊 各源失败密钥数:")
                for source, count in failed_by_source.items():
                    print(f"  {source}: {count}")
            else:
                print(f"✅ 所有源的密钥都运行正常")
                
            # 显示详细统计
            detailed_stats = stats.get('detailed_stats', {})
            if detailed_stats:
                print(f"\n📈 详细统计信息:")
                for source, info in detailed_stats.items():
                    print(f"  {source}:")
                    print(f"    - 失败密钥数: {info.get('failed_keys', 0)}")
                    print(f"    - 总失败次数: {info.get('total_failures', 0)}")
                    print(f"    - 受影响模型数: {len(info.get('models_affected', []))}")
        else:
            print(f"❌ 获取统计信息失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 获取统计信息异常: {str(e)}")

def check_source_availability():
    """检查各源的可用性"""
    print("\n🔍 检查源可用性")
    test_sources = get_available_sources()
    
    if not test_sources:
        print("❌ 无法获取源列表")
        return
    
    print(f"检查 {len(test_sources)} 个源...")
    
    for source in test_sources:
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_KEY_MANAGER_URL}/get_apikey",
                json={"source_name": source},
                timeout=5
            )
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            if response.status_code == 200:
                print(f"  ✅ {source}: 可用 ({response_time:.1f}ms)")
            elif response.status_code == 404:
                print(f"  ❌ {source}: 未找到源 ({response_time:.1f}ms)")
            else:
                print(f"  ⚠️  {source}: HTTP {response.status_code} ({response_time:.1f}ms)")
        except Exception as e:
            print(f"  💥 {source}: 异常 - {str(e)}")

if __name__ == "__main__":
    print("🧪 API密钥管理器性能测试工具")
    print("=" * 60)
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{API_KEY_MANAGER_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API密钥管理器服务不可用: HTTP {response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到API密钥管理器服务: {str(e)}")
        print(f"💡 请确保服务运行在 {API_KEY_MANAGER_URL}")
        exit(1)
    
    print(f"✅ API密钥管理器服务正常运行")
    
    # 执行测试
    check_source_availability()
    test_stats_endpoint()
    test_cache_refresh()
    test_concurrent_performance()
    
    print("\n🎉 测试完成!") 