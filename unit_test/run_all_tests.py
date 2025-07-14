#!/usr/bin/env python3
"""
测试运行器：提供统一的接口来运行各种测试
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# 测试脚本列表
TEST_SCRIPTS = {
    "quick": {
        "script": "test_new_features.py",
        "description": "快速功能验证测试",
        "estimated_time": "1-2分钟"
    },
    "comprehensive": {
        "script": "comprehensive_test_suite.py",
        "description": "全面测试套件（单元测试、集成测试、压力测试）",
        "estimated_time": "10-15分钟"
    },
    "performance": {
        "script": "performance_test.py",
        "description": "性能测试（响应时间、并发、负载）",
        "estimated_time": "5-10分钟"
    },
    "stress": {
        "script": "performance_test.py stress",
        "description": "高强度压力测试",
        "estimated_time": "2-5分钟"
    },
    "edge": {
        "script": "edge_case_tests.py",
        "description": "边界情况和异常处理测试",
        "estimated_time": "5-8分钟"
    },
    "all": {
        "script": "ALL",
        "description": "运行所有测试（除压力测试）",
        "estimated_time": "20-30分钟"
    }
}

def print_menu():
    """打印测试菜单"""
    print("\n" + "="*60)
    print("外部WebAPI LLM系统测试运行器")
    print("="*60)
    print("\n可用的测试选项：\n")
    
    for key, info in TEST_SCRIPTS.items():
        print(f"  {key:<15} - {info['description']}")
        print(f"  {'':15}   预计时间: {info['estimated_time']}")
        print()

def run_test(test_name):
    """运行指定的测试"""
    if test_name not in TEST_SCRIPTS:
        print(f"错误：未知的测试类型 '{test_name}'")
        return False
    
    test_info = TEST_SCRIPTS[test_name]
    
    print(f"\n开始运行: {test_info['description']}")
    print(f"预计时间: {test_info['estimated_time']}")
    print("-" * 60)
    
    start_time = time.time()
    
    if test_name == "all":
        # 运行所有测试（除了压力测试）
        test_sequence = ["quick", "comprehensive", "performance", "edge"]
        all_success = True
        
        for sub_test in test_sequence:
            print(f"\n\n{'='*60}")
            print(f"运行测试组: {TEST_SCRIPTS[sub_test]['description']}")
            print(f"{'='*60}")
            
            success = run_single_test(TEST_SCRIPTS[sub_test]['script'])
            if not success:
                all_success = False
                print(f"\n警告: {sub_test} 测试失败")
            
            # 测试之间短暂休息
            if sub_test != test_sequence[-1]:
                print("\n等待5秒后继续下一个测试...")
                time.sleep(5)
        
        elapsed_time = time.time() - start_time
        print(f"\n\n所有测试完成！总耗时: {elapsed_time/60:.1f} 分钟")
        return all_success
    else:
        # 运行单个测试
        success = run_single_test(test_info['script'])
        elapsed_time = time.time() - start_time
        print(f"\n测试完成！耗时: {elapsed_time/60:.1f} 分钟")
        return success

def run_single_test(script_command):
    """运行单个测试脚本"""
    try:
        # 分割命令和参数
        parts = script_command.split()
        script = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # 构建完整的命令
        cmd = [sys.executable, script] + args
        
        # 运行测试脚本
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,  # 直接显示输出
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"运行测试时出错: {str(e)}")
        return False

def generate_test_report():
    """生成测试报告汇总"""
    print("\n生成测试报告汇总...")
    
    # 查找所有测试结果目录
    result_dirs = [
        "test_results",
        "performance_results",
        "edge_case_results"
    ]
    
    report_content = []
    report_content.append("# 测试报告汇总")
    report_content.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for dir_name in result_dirs:
        if os.path.exists(dir_name):
            report_content.append(f"\n## {dir_name}")
            
            # 列出最新的几个结果文件
            files = sorted([f for f in os.listdir(dir_name) if f.endswith('.json')], reverse=True)[:5]
            
            if files:
                report_content.append("\n最新结果文件：")
                for file in files:
                    report_content.append(f"- {file}")
            else:
                report_content.append("\n暂无测试结果")
    
    # 保存报告
    report_path = "test_report_summary.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_content))
    
    print(f"测试报告已保存到: {report_path}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行参数模式
        test_name = sys.argv[1]
        
        if test_name == "help":
            print_menu()
            print("\n使用方法: python run_all_tests.py [测试类型]")
            print("例如: python run_all_tests.py quick")
        elif test_name == "report":
            generate_test_report()
        else:
            run_test(test_name)
    else:
        # 交互式菜单模式
        while True:
            print_menu()
            print("其他选项：")
            print("  report         - 生成测试报告汇总")
            print("  exit           - 退出\n")
            
            choice = input("请选择要运行的测试 (输入选项名称): ").strip().lower()
            
            if choice == "exit":
                print("退出测试运行器")
                break
            elif choice == "report":
                generate_test_report()
                input("\n按回车键继续...")
            elif choice in TEST_SCRIPTS:
                print(f"\n确认运行 '{TEST_SCRIPTS[choice]['description']}'? (y/n): ", end="")
                confirm = input().strip().lower()
                
                if confirm == 'y':
                    run_test(choice)
                    input("\n按回车键继续...")
                else:
                    print("取消运行")
            else:
                print(f"\n错误：未知的选项 '{choice}'")
                input("按回车键继续...")

if __name__ == "__main__":
    main() 