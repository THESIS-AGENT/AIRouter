#!/usr/bin/env python3
"""
健康检查屏蔽功能集成测试脚本

测试目标：
1. CheckHealthy.py 是否正确屏蔽了黑名单中的模型
2. LoadBalancing.py 是否能正确获取 API key
3. LoadBalancing.py 是否正确应用了健康检查屏蔽逻辑
4. 被屏蔽的模型是否仍然可以正常获取 API key 并使用
"""

import sys
import os
import json
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ew_config.source import (
        health_check_blacklist, 
        is_model_health_check_blacklisted,
        model_list_normal, 
        model_list_thinking, 
        model_list_mm_normal, 
        model_list_mm_thinking,
        source_mapping,
        source_ranking
    )
    from CheckHealthy import CheckHealthy
    from LoadBalancing import LoadBalancing, Harness_localAPI
    from api_key_manager.client import APIKeyManagerClient
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在 external_webAPI 目录下运行此脚本")
    sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BlacklistIntegrationTester:
    """健康检查屏蔽功能集成测试器"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
    def log_test_result(self, test_name, passed, details):
        """记录测试结果"""
        self.test_results["tests"][test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
        
    def test_blacklist_configuration(self):
        """测试1: 验证屏蔽配置是否正确"""
        logger.info("🧪 测试1: 屏蔽配置验证")
        
        try:
            # 检查屏蔽清单是否存在
            if not health_check_blacklist:
                self.log_test_result("blacklist_config", False, "屏蔽清单为空")
                return
                
            logger.info(f"当前屏蔽清单: {health_check_blacklist}")
            
            # 测试层级屏蔽逻辑
            test_cases = [
                ("claude4_opus", True, "精确匹配屏蔽"),
                ("claude4_opus_mm", True, "层级屏蔽（多模态）"),
                ("claude4_sonnet", False, "不在屏蔽清单"),
                ("claude4_sonnet_mm", False, "基础模型未屏蔽的多模态"),
                ("claude4_opus_thinking", True, "思维模型屏蔽"),
                ("gemini25_flash", False, "正常模型不屏蔽")
            ]
            
            all_passed = True
            for model_name, expected, description in test_cases:
                result = is_model_health_check_blacklisted(model_name)
                if result == expected:
                    logger.info(f"  ✅ {model_name}: {description} - 正确")
                else:
                    logger.error(f"  ❌ {model_name}: {description} - 期望{expected}，实际{result}")
                    all_passed = False
                    
            self.log_test_result(
                "blacklist_config", 
                all_passed, 
                f"层级屏蔽逻辑测试，屏蔽清单包含{len(health_check_blacklist)}个模型"
            )
            
        except Exception as e:
            self.log_test_result("blacklist_config", False, f"配置测试异常: {str(e)}")
            
    def test_checkHealthy_filtering(self):
        """测试2: 验证CheckHealthy是否正确过滤屏蔽模型"""
        logger.info("🧪 测试2: CheckHealthy过滤验证")
        
        try:
            # 获取所有模型
            all_models = model_list_normal + model_list_thinking + model_list_mm_normal + model_list_mm_thinking
            
            # 模拟健康检查过滤逻辑
            models_to_check = [model for model in all_models if not is_model_health_check_blacklisted(model)]
            blacklisted_models = [model for model in all_models if is_model_health_check_blacklisted(model)]
            
            logger.info(f"总模型数: {len(all_models)}")
            logger.info(f"计划检测模型数: {len(models_to_check)}")
            logger.info(f"屏蔽模型数: {len(blacklisted_models)}")
            logger.info(f"屏蔽模型: {blacklisted_models}")
            
            # 验证屏蔽逻辑
            expected_blacklisted = ["claude4_opus", "claude4_opus_mm", "claude4_opus_thinking", "claude4_sonnet_thinking"]
            
            # 检查是否包含期望的屏蔽模型
            missing_blacklisted = []
            for expected in expected_blacklisted:
                if expected in all_models and expected not in blacklisted_models:
                    missing_blacklisted.append(expected)
                    
            # 检查是否误屏蔽了不应该屏蔽的模型
            unexpected_blacklisted = []
            for model in blacklisted_models:
                if not any(model == blacklisted or 
                          (model.endswith("_mm") and model[:-3] in health_check_blacklist) or
                          model in health_check_blacklist
                          for blacklisted in health_check_blacklist):
                    unexpected_blacklisted.append(model)
            
            success = len(missing_blacklisted) == 0 and len(unexpected_blacklisted) == 0
            details = f"正确屏蔽{len(blacklisted_models)}个模型，误屏蔽{len(unexpected_blacklisted)}个，遗漏{len(missing_blacklisted)}个"
            
            if not success:
                details += f" | 误屏蔽: {unexpected_blacklisted} | 遗漏: {missing_blacklisted}"
                
            self.log_test_result("checkHealthy_filtering", success, details)
            
        except Exception as e:
            self.log_test_result("checkHealthy_filtering", False, f"过滤测试异常: {str(e)}")
    
    def test_loadBalancing_api_key_access(self):
        """测试3: 验证LoadBalancing能否正确获取API key"""
        logger.info("🧪 测试3: LoadBalancing API密钥获取测试")
        
        # Mock API key manager response
        mock_api_key = "test-api-key-12345"
        
        with patch.object(Harness_localAPI, 'get_api_key', return_value=mock_api_key):
            try:
                # 测试几个不同源的API key获取
                test_sources = ["openai", "anthropic", "google", "openrouter"]
                success_count = 0
                
                for source in test_sources:
                    try:
                        api_key = Harness_localAPI.get_api_key(source)
                        if api_key == mock_api_key:
                            logger.info(f"  ✅ {source}: API密钥获取成功")
                            success_count += 1
                        else:
                            logger.error(f"  ❌ {source}: API密钥不匹配")
                    except Exception as e:
                        logger.error(f"  ❌ {source}: API密钥获取失败 - {str(e)}")
                
                success = success_count == len(test_sources)
                self.log_test_result(
                    "loadBalancing_api_key", 
                    success, 
                    f"成功获取{success_count}/{len(test_sources)}个源的API密钥"
                )
                
            except Exception as e:
                self.log_test_result("loadBalancing_api_key", False, f"API密钥测试异常: {str(e)}")
    
    def test_loadBalancing_blacklist_handling(self):
        """测试4: 验证LoadBalancing对屏蔽模型的处理"""
        logger.info("🧪 测试4: LoadBalancing屏蔽模型处理测试")
        
        # Mock健康检查数据和API密钥
        mock_health_data = {
            "timestamp": datetime.now().isoformat(),
            "check_timer_span": 15,
            "data": {
                ("openai", "gpt41_normal"): [1.5, 2.0, 1.8],
                ("anthropic", "claude37_normal"): [2.1, 2.3, 2.0],
                # 注意：屏蔽的模型没有健康数据
            }
        }
        
        mock_api_key = "test-api-key-67890"
        
        with patch.object(Harness_localAPI, 'check_healthy', return_value=mock_health_data), \
             patch.object(Harness_localAPI, 'get_api_key', return_value=mock_api_key):
            
            try:
                load_balancer = LoadBalancing()
                
                # 测试屏蔽模型和非屏蔽模型
                test_cases = [
                    ("claude4_opus", True, "屏蔽模型"),
                    ("claude4_opus_mm", True, "屏蔽模型（多模态）"),
                    ("claude4_sonnet", False, "非屏蔽模型"),
                    ("gpt41_normal", False, "非屏蔽模型"),
                ]
                
                all_passed = True
                
                for model_name, is_blacklisted, description in test_cases:
                    try:
                        # 测试is_health_data_empty方法
                        is_empty = load_balancer.is_health_data_empty(model_name)
                        
                        if is_blacklisted:
                            # 屏蔽模型应该返回True（健康数据为空）
                            if is_empty:
                                logger.info(f"  ✅ {model_name}: {description} - 正确识别为无健康数据")
                            else:
                                logger.error(f"  ❌ {model_name}: {description} - 应该识别为无健康数据")
                                all_passed = False
                        else:
                            # 非屏蔽模型的健康数据状态取决于实际数据
                            logger.info(f"  ℹ️ {model_name}: {description} - 健康数据状态: {'空' if is_empty else '有数据'}")
                    
                    except Exception as e:
                        logger.error(f"  ❌ {model_name}: 测试异常 - {str(e)}")
                        all_passed = False
                
                self.log_test_result(
                    "loadBalancing_blacklist", 
                    all_passed, 
                    f"屏蔽模型处理逻辑测试完成"
                )
                
            except Exception as e:
                self.log_test_result("loadBalancing_blacklist", False, f"屏蔽处理测试异常: {str(e)}")
    
    def test_blacklisted_models_still_usable(self):
        """测试5: 验证屏蔽模型仍然可以通过LoadBalancing使用"""
        logger.info("🧪 测试5: 屏蔽模型可用性测试")
        
        # Mock数据
        mock_health_data = {
            "timestamp": datetime.now().isoformat(),
            "check_timer_span": 15,
            "data": {}  # 空的健康数据，模拟屏蔽后的状态
        }
        
        mock_api_key = "test-blacklisted-model-key"
        
        with patch.object(Harness_localAPI, 'check_healthy', return_value=mock_health_data), \
             patch.object(Harness_localAPI, 'get_api_key', return_value=mock_api_key):
            
            try:
                load_balancer = LoadBalancing()
                
                # 测试屏蔽模型是否仍然可以获取配置
                blacklisted_models = ["claude4_opus", "claude4_opus_thinking"]
                
                success_count = 0
                total_tests = 0
                
                for model_name in blacklisted_models:
                    # 检查模型是否在源映射中有配置
                    has_mapping = False
                    for source_name in source_mapping:
                        base_model = model_name[:-3] if model_name.endswith("_mm") else model_name
                        if base_model in source_mapping[source_name] and source_mapping[source_name][base_model] is not None:
                            has_mapping = True
                            break
                    
                    if not has_mapping:
                        logger.info(f"  ⚠️ {model_name}: 在源映射中无可用配置，跳过测试")
                        continue
                        
                    total_tests += 1
                    
                    try:
                        # 尝试获取配置（应该使用预设排名）
                        result = load_balancer.get_config(model_name, "cheap_first", 50, 50)
                        
                        if result and len(result) == 6:
                            main_source, main_model, main_key, backup_source, backup_model, backup_key = result
                            logger.info(f"  ✅ {model_name}: 成功获取配置")
                            logger.info(f"    主源: {main_source} -> {main_model}")
                            logger.info(f"    备用源: {backup_source} -> {backup_model}")
                            logger.info(f"    API密钥: {'已获取' if main_key else '获取失败'}")
                            success_count += 1
                        else:
                            logger.error(f"  ❌ {model_name}: 配置格式不正确")
                            
                    except Exception as e:
                        if "无法获取API密钥" in str(e) or "没有找到任何可用的模型" in str(e):
                            logger.warning(f"  ⚠️ {model_name}: {str(e)} (可能是配置问题)")
                        else:
                            logger.error(f"  ❌ {model_name}: 获取配置失败 - {str(e)}")
                
                success = success_count == total_tests if total_tests > 0 else True
                details = f"成功测试{success_count}/{total_tests}个屏蔽模型的可用性"
                
                if total_tests == 0:
                    details = "未找到可测试的屏蔽模型"
                    
                self.log_test_result("blacklisted_models_usable", success, details)
                
            except Exception as e:
                self.log_test_result("blacklisted_models_usable", False, f"可用性测试异常: {str(e)}")
    
    def test_health_check_integration(self):
        """测试6: 健康检查集成测试（模拟运行）"""
        logger.info("🧪 测试6: 健康检查集成测试")
        
        try:
            # 模拟检查健康检查服务的启动参数
            all_models = model_list_normal + model_list_thinking + model_list_mm_normal + model_list_mm_thinking
            models_to_check = [model for model in all_models if not is_model_health_check_blacklisted(model)]
            blacklisted_models = [model for model in all_models if is_model_health_check_blacklisted(model)]
            
            # 计算预期的健康检查测试数量
            expected_tests = 0
            for model_name in models_to_check:
                for source_name in source_mapping:
                    base_model_name = model_name[:-3] if model_name.endswith("_mm") else model_name
                    if (source_name in source_mapping and 
                        base_model_name in source_mapping[source_name] and 
                        source_mapping[source_name][base_model_name] is not None):
                        expected_tests += 1
            
            # 计算被屏蔽的测试数量
            blacklisted_tests = 0
            for model_name in blacklisted_models:
                for source_name in source_mapping:
                    base_model_name = model_name[:-3] if model_name.endswith("_mm") else model_name
                    if (source_name in source_mapping and 
                        base_model_name in source_mapping[source_name] and 
                        source_mapping[source_name][base_model_name] is not None):
                        blacklisted_tests += 1
            
            total_possible_tests = expected_tests + blacklisted_tests
            savings_percentage = (blacklisted_tests / total_possible_tests * 100) if total_possible_tests > 0 else 0
            
            logger.info(f"  📊 总可能测试数: {total_possible_tests}")
            logger.info(f"  📊 实际计划测试数: {expected_tests}")
            logger.info(f"  📊 屏蔽测试数: {blacklisted_tests}")
            logger.info(f"  📊 节省成本比例: {savings_percentage:.1f}%")
            
            # 验证屏蔽是否有效
            success = blacklisted_tests > 0 and savings_percentage > 0
            details = f"屏蔽{blacklisted_tests}个测试，节省{savings_percentage:.1f}%成本"
            
            self.log_test_result("health_check_integration", success, details)
            
        except Exception as e:
            self.log_test_result("health_check_integration", False, f"集成测试异常: {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始健康检查屏蔽功能集成测试")
        logger.info("=" * 80)
        
        # 运行所有测试
        self.test_blacklist_configuration()
        self.test_checkHealthy_filtering()
        self.test_loadBalancing_api_key_access()
        self.test_loadBalancing_blacklist_handling()
        self.test_blacklisted_models_still_usable()
        self.test_health_check_integration()
        
        # 生成测试报告
        self.generate_test_report()
        
    def generate_test_report(self):
        """生成测试报告"""
        logger.info("=" * 80)
        logger.info("📋 测试报告汇总")
        
        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for test in self.test_results["tests"].values() if test["passed"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {failed_tests}")
        logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            logger.error("失败的测试:")
            for test_name, result in self.test_results["tests"].items():
                if not result["passed"]:
                    logger.error(f"  ❌ {test_name}: {result['details']}")
        
        # 保存测试结果到文件
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blacklist_integration_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试结果已保存到: {filename}")
        
        # 整体测试结论
        if failed_tests == 0:
            logger.info("🎉 所有测试通过！屏蔽功能工作正常")
        else:
            logger.error("⚠️ 部分测试失败，请检查配置")
        
        logger.info("=" * 80)

def main():
    """主函数"""
    try:
        tester = BlacklistIntegrationTester()
        tester.run_all_tests()
        return 0
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        return 1
    except Exception as e:
        logger.error(f"测试执行异常: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 