#!/usr/bin/env python3
"""
测试结果分析脚本：分析测试结果并提供改进建议
"""

import json
import os
from datetime import datetime
import statistics

def analyze_performance_results(results_file):
    """分析性能测试结果"""
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print("\n=== 性能测试分析 ===")
    
    summary = data.get('summary', {})
    
    # 分析响应时间
    print("\n1. 响应时间分析:")
    response_times = []
    for test_name, metrics in summary.items():
        if 'response_time' in metrics and metrics['response_time']['mean'] > 0:
            mean_time = metrics['response_time']['mean']
            p95_time = metrics['response_time']['p95']
            max_time = metrics['response_time']['max']
            response_times.append(mean_time)
            
            print(f"  {test_name}:")
            print(f"    平均: {mean_time:.2f}s")
            print(f"    P95: {p95_time:.2f}s")
            print(f"    最大: {max_time:.2f}s")
            
            # 性能评估
            if mean_time > 5:
                print(f"    ⚠️  响应时间过长，建议优化")
            elif mean_time > 3:
                print(f"    ⚡ 响应时间较长，可以改进")
            else:
                print(f"    ✅ 响应时间良好")
    
    # 分析并发性能
    print("\n2. 并发性能分析:")
    if 'concurrent_load' in summary:
        concurrent = summary['concurrent_load']
        throughput = concurrent.get('throughput', {}).get('mean', 0)
        success_rate = concurrent.get('success_rate', {}).get('mean', 0)
        
        print(f"  吞吐量: {throughput:.2f} req/s")
        print(f"  成功率: {success_rate*100:.1f}%")
        
        if throughput < 1:
            print("  ⚠️  吞吐量较低，建议增加并发处理能力")
        elif throughput < 5:
            print("  ⚡ 吞吐量中等，有提升空间")
        else:
            print("  ✅ 吞吐量良好")
    
    # 分析稳定性
    print("\n3. 稳定性分析:")
    for test_name, metrics in summary.items():
        if 'response_time' in metrics:
            mean_time = metrics['response_time']['mean']
            stdev = metrics['response_time']['stdev']
            if mean_time > 0:
                cv = stdev / mean_time  # 变异系数
                if cv > 0.5:
                    print(f"  {test_name}: ⚠️  不稳定 (CV={cv:.2f})")
                elif cv > 0.3:
                    print(f"  {test_name}: ⚡ 较稳定 (CV={cv:.2f})")
                else:
                    print(f"  {test_name}: ✅ 稳定 (CV={cv:.2f})")
    
    return summary

def analyze_edge_case_results(results_file):
    """分析边界测试结果"""
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print("\n=== 边界测试分析 ===")
    
    summary = data.get('summary', {})
    tests = data.get('tests', [])
    
    print(f"\n总测试数: {summary['total']}")
    print(f"通过: {summary['passed']} ({summary['passed']/summary['total']*100:.1f}%)")
    print(f"失败: {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
    print(f"警告: {summary['warnings']} ({summary['warnings']/summary['total']*100:.1f}%)")
    
    # 分析失败的测试
    failed_tests = [t for t in tests if t['status'] == 'failed']
    if failed_tests:
        print("\n失败的测试类型:")
        failed_categories = {}
        for test in failed_tests:
            category = test['test_name'].split('_')[0]
            failed_categories[category] = failed_categories.get(category, 0) + 1
        
        for category, count in failed_categories.items():
            print(f"  {category}: {count} 个失败")
    
    # 分析警告
    warning_tests = [t for t in tests if t['status'] == 'warning']
    if warning_tests:
        print("\n需要关注的警告:")
        for test in warning_tests[:5]:  # 只显示前5个
            print(f"  - {test['test_name']}: {test['description']}")
    
    return summary

def generate_recommendations():
    """生成改进建议"""
    print("\n=== 改进建议 ===")
    
    recommendations = [
        {
            "category": "性能优化",
            "items": [
                "考虑实现请求缓存机制，减少重复请求",
                "优化模型选择算法，减少帕累托计算开销",
                "实现连接池复用，减少连接建立时间",
                "对于超时恢复测试，使用更短的测试提示词"
            ]
        },
        {
            "category": "稳定性改进",
            "items": [
                "增加重试机制的智能判断，避免无效重试",
                "实现更细粒度的错误处理和恢复策略",
                "添加熔断机制，防止级联失败",
                "优化健康检查频率和策略"
            ]
        },
        {
            "category": "边界处理",
            "items": [
                "完善输入验证，提前拒绝无效参数",
                "优化超大输入的处理策略",
                "改进多模态图像验证逻辑",
                "增加更多的参数默认值处理"
            ]
        },
        {
            "category": "监控和日志",
            "items": [
                "添加更详细的性能指标监控",
                "实现请求追踪和分析",
                "优化日志级别和输出格式",
                "添加告警机制"
            ]
        }
    ]
    
    for rec in recommendations:
        print(f"\n{rec['category']}:")
        for item in rec['items']:
            print(f"  • {item}")

def main():
    """主函数"""
    print("="*60)
    print("测试结果分析报告")
    print("="*60)
    
    # 查找最新的测试结果文件
    performance_dir = "performance_results"
    edge_case_dir = "edge_case_results"
    
    # 分析性能测试结果
    if os.path.exists(performance_dir):
        files = sorted([f for f in os.listdir(performance_dir) if f.endswith('.json')], reverse=True)
        if files:
            latest_perf = os.path.join(performance_dir, files[0])
            print(f"\n分析文件: {latest_perf}")
            analyze_performance_results(latest_perf)
    
    # 分析边界测试结果
    if os.path.exists(edge_case_dir):
        files = sorted([f for f in os.listdir(edge_case_dir) if f.endswith('.json')], reverse=True)
        if files:
            latest_edge = os.path.join(edge_case_dir, files[0])
            print(f"\n分析文件: {latest_edge}")
            analyze_edge_case_results(latest_edge)
    
    # 生成改进建议
    generate_recommendations()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main() 