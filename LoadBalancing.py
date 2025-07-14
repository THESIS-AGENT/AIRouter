try:
    from .ew_config.source import source_price, source_ranking, source_mapping, model_list_normal, model_list_thinking, model_list_mm_normal, model_list_mm_thinking, health_check_blacklist, is_model_health_check_blacklisted
    from .ew_config.api_keys import pool_mapping
except ImportError:
    from ew_config.source import source_price, source_ranking, source_mapping, model_list_normal, model_list_thinking, model_list_mm_normal, model_list_mm_thinking, health_check_blacklist, is_model_health_check_blacklisted
    from ew_config.api_keys import pool_mapping
import numpy as np
from datetime import datetime
import requests
import os
import logging
import random

"""目标: 在需要一个模型时, 输入自定义模型名, 推出最满足当前需求的源下模型,
以及主模型和备用模型, 各自源下模型负载均衡后的api_key.
"""

# 健康检查是每15分钟一次, 容忍4次的意思是, 如果最新出现1次接口挂掉的情况.
# 则接下来的1个小时内(4*15), 都不会优先使用来自于该源的该模型.
TOLERANCE_TIMES = int(os.environ.get("TOLERANCE_TIMES", 4))
API_HEALTH_CHECK_URL = os.environ.get("API_HEALTH_CHECK_URL", "http://localhost:8001/check_healthy")
API_KEY_MANAGER_URL = os.environ.get("API_KEY_MANAGER_URL", "http://localhost:8002")
API_KEY_MANAGER_GET_ENDPOINT = os.environ.get("API_KEY_MANAGER_GET_ENDPOINT", "/get_apikey")
INNER_TIMEOUT = int(os.environ.get("INNER_TIMEOUT", 5))


class Harness_localAPI:
    @staticmethod
    def check_healthy():
        """从本地健康检查服务获取API健康状态数据
        
        Returns:
            dict: 包含时间戳、检查间隔和健康数据的字典
        """
        logger = logging.getLogger(__name__)
        # 防止日志向上传播，避免重复打印
        logger.propagate = False
        try:
            # 调用本地健康检查服务API
            logger.info("正在调用健康检查服务API获取健康状态数据")
            response = requests.get(API_HEALTH_CHECK_URL, timeout=INNER_TIMEOUT)
            if response.status_code == 200:
                result = response.json()
                # 将字符串键转换为元组键
                if "data" in result:
                    result["data"] = {tuple(key.split("|")): [np.nan if v is None else v for v in value] for key, value in result["data"].items()}
                logger.info("成功获取健康状态数据")
                return result
            else:
                # 如果API调用失败，返回空数据结构和当前时间
                logger.error(f"健康检查API返回错误状态码: {response.status_code}")
                return {"timestamp": datetime.now().isoformat(), "check_timer_span": 15, "data": {}}
        except Exception as e:
            # 出现异常时记录错误并返回空数据结构
            logger.error(f"获取健康状态数据时出错: {str(e)}")
            return {"timestamp": datetime.now().isoformat(), "check_timer_span": 15, "data": {}}

    @staticmethod
    def get_api_key(source_name):
        """从API密钥管理服务获取API密钥，失败时使用备用方案
        
        Args:
            source_name (str): 源名称
            
        Returns:
            str: API密钥
            
        Raises:
            Exception: 如果主备用方案都无法获取API密钥
        """
        logger = logging.getLogger(__name__)
        # 防止日志向上传播，避免重复打印
        logger.propagate = False
        
        try:
            # 优先尝试调用API密钥管理服务API
            response = requests.post(
                f"{API_KEY_MANAGER_URL}{API_KEY_MANAGER_GET_ENDPOINT}", 
                json={"source_name": source_name}, 
                timeout=INNER_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"成功从API密钥管理服务获取 {source_name} 的API密钥")
                return result["api_key"]
            else:
                # 如果API调用失败，记录警告并尝试备用方案
                logger.warning(f"API密钥服务返回错误状态码: {response.status_code}，尝试使用备用方案")
                raise Exception(f"API service returned status code: {response.status_code}")
                
        except Exception as e:
            # 连接失败时，尝试使用备用方案：从pool_mapping中获取API密钥
            logger.warning(f"无法连接到API密钥管理服务 (已离线): {str(e)}，使用兜底离线配获取API密钥")
            
            try:
                if source_name not in pool_mapping:
                    raise ValueError(f"兜底离线配中未找到源 '{source_name}' 的配置")
                
                source_pool = pool_mapping[source_name]
                if not source_pool:
                    raise ValueError(f"源 '{source_name}' 的API密钥池为空")
                
                # 从所有账户的所有API密钥中随机选择一个
                all_api_keys = []
                for account, keys in source_pool.items():
                    for key_info in keys:
                        if "api_key" in key_info:
                            all_api_keys.append(key_info["api_key"])
                
                if not all_api_keys:
                    raise ValueError(f"源 '{source_name}' 的兜底离线配中没有有效的API密钥")
                
                selected_api_key = random.choice(all_api_keys)
                logger.warning(f"使用兜底离线配置为源 '{source_name}' 随机选择了一个API密钥")
                return selected_api_key
                
            except Exception as backup_e:
                # 备用方案也失败时，抛出异常
                error_msg = f"主方案和备用方案都无法获取源 '{source_name}' 的API密钥。主方案错误: {str(e)}，备用方案错误: {str(backup_e)}"
                logger.error(error_msg)
                raise Exception(error_msg)


class LoadBalancing:
    def __init__(self) -> None:
        """初始化LoadBalancing实例，获取健康检查数据和配置"""
        # 这里要维护一个包含滑动窗口逻辑的, 每个供应商的每个模型的表现情况队列.
        # 然后先按照损坏概率去降序排序.
        # 再按照执行时间去降序排序.
        self.healthy = Harness_localAPI.check_healthy()
        self.source_price = source_price
        self.source_ranking = source_ranking
        self.source_mapping = source_mapping
        # 添加日志记录器
        self.logger = logging.getLogger(__name__)
        # 防止日志向上传播，避免重复打印
        self.logger.propagate = False


    def _check_valid_model(self, source_name, model_name):
        """检查模型是否在源上有效
        
        Args:
            source_name (str): 源名称
            model_name (str): 模型名称
            
        Returns:
            bool: 如果模型有效返回True，否则返回False
        """
        # 处理多模态模型的情况
        base_model_name = model_name[:-3] if model_name.endswith("_mm") else model_name
        
        # 检查映射是否存在且非None
        if (source_name in self.source_mapping and 
            base_model_name in self.source_mapping[source_name] and 
            self.source_mapping[source_name][base_model_name] is not None):
            return True
        return False

    def get_combinedRanking(self, ranking_1, ranking_2, weight):
        """融合两个不同指标的排序
        
        将两个不同指标的排序结果按给定权重融合为一个新的排序结果。
        
        Args:
            ranking_1 (dict): 第一个指标的排序结果
            ranking_2 (dict): 第二个指标的排序结果
            weight (float): ranking_2的权重，范围[0,1]
            
        Returns:
            dict: 融合后的排序结果
        """
        ranking_3 = {}
        
        len_1 = len(ranking_1)
        len_2 = len(ranking_2)
        
        # 创建副本避免修改原始数据
        tmp_ranking_1 = ranking_1.copy()
        tmp_ranking_2 = ranking_2.copy()
        
        # 处理ranking_1中的所有键
        for key_1 in ranking_1:
            if key_1 in ranking_2:
                # 如果键在两个排序中都存在，按权重融合
                ranking_3[key_1] = ranking_1[key_1] * (1 - weight) + ranking_2[key_1] * weight
            else:
                # 如果键只在ranking_1中存在，将其在ranking_2中的排名设为最低
                tmp_ranking_2[key_1] = len_2 + 1
                ranking_3[key_1] = ranking_1[key_1] * (1 - weight) + tmp_ranking_2[key_1] * weight
                
        # 处理ranking_2中的所有键
        for key_2 in ranking_2:
            if key_2 not in ranking_1:
                # 如果键只在ranking_2中存在，将其在ranking_1中的排名设为最低
                tmp_ranking_1[key_2] = len_1 + 1
                ranking_3[key_2] = tmp_ranking_1[key_2] * (1 - weight) + ranking_2[key_2] * weight
        
        return ranking_3

    def is_health_data_empty(self, model_name):
        """检查健康数据是否为空
        
        检查指定模型在所有源上的健康数据是否全部为空数组。
        对于健康检测屏蔽清单中的模型，始终返回True以强制使用预设排名。
        
        Args:
            model_name (str): 要检查的模型名称
            
        Returns:
            bool: 如果所有健康数据都是空数组则返回True，否则返回False
        """
        try:
            # 检查模型是否在健康检测屏蔽清单中
            if model_name in health_check_blacklist:
                self.logger.info(f"模型 {model_name} 在健康检测屏蔽清单中，强制使用预设排名")
                return True
            
            # 检查健康数据是否有效
            if not self.healthy or "data" not in self.healthy or not self.healthy["data"]:
                self.logger.warning(f"模型 {model_name} 的健康数据为空或无效")
                return True
            
            # 不再处理多模态模型名称，直接使用完整的model_name
                
            # 寻找该模型在任意源上的非空数据
            for key, value in self.healthy["data"].items():
                try:
                    if len(key) >= 2 and key[1] == model_name and value and len(value) > 0:
                        return False
                except Exception as e:
                    self.logger.warning(f"处理健康数据键 {key} 时出错: {str(e)}")
                    continue
                    
            self.logger.info(f"模型 {model_name} 在所有源上的健康数据均为空")
            return True  # 所有源的该模型数据均为空
        except Exception as e:
            self.logger.error(f"检查模型 {model_name} 的健康数据时出错: {str(e)}")
            return True  # 出错时假设数据为空，使用预设排名
    
    def get_sources_from_ranking(self, model_name):
        """基于预设排名获取源和模型配置
        
        当健康检查数据为空时，基于预设的源排名获取配置。
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            tuple: 包含主源和备用源的配置信息
            
        Raises:
            ValueError: 如果找不到可用的源
        """
        try:
            # 检查是否为屏蔽模型
            if is_model_health_check_blacklisted(model_name):
                self.logger.info(f"🚫 模型 {model_name} 在健康检测屏蔽清单中，基于预设排名选择源")
            else:
                self.logger.info(f"基于预设排名为模型 {model_name} 选择源")
            
            # 根据source_ranking选择排名靠前的源
            sorted_sources = sorted(self.source_ranking.keys(), key=lambda s: self.source_ranking[s])
            
            # 找出可用的源（即映射中有此模型的源）
            available_sources = []
            for source in sorted_sources:
                if self._check_valid_model(source, model_name):
                    available_sources.append(source)

            if not available_sources:
                error_msg = f"在预设排名中找不到模型 {model_name} 的可用源"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 选择主源和备用源
            main_source = available_sources[0]
            backup_source = available_sources[1] if len(available_sources) > 1 else main_source
            
            # 获取模型名称和API密钥
            main_source_model_name = self._get_actual_model_name(main_source, model_name)
            backup_source_model_name = self._get_actual_model_name(backup_source, model_name)
            
            self.logger.info(f"选择主源 {main_source} 和备用源 {backup_source} 为模型 {model_name}")
            
            try:
                main_api_key = Harness_localAPI.get_api_key(main_source)
                backup_api_key = Harness_localAPI.get_api_key(backup_source)
            except Exception as e:
                self.logger.error(f"获取API密钥时出错: {str(e)}")
                raise ValueError(f"无法获取API密钥: {str(e)}")
            
            return main_source, main_source_model_name, main_api_key, backup_source, backup_source_model_name, backup_api_key
        except Exception as e:
            self.logger.error(f"基于预设排名选择源时出错: {str(e)}")
            raise

    def _get_actual_model_name(self, source_name, model_name):
        """获取实际模型名称，处理多模态模型
        
        Args:
            source_name (str): 源名称
            model_name (str): 模型名称
            
        Returns:
            str: 实际模型名称或None
        """
        # 获取基础模型名（去掉_mm后缀）
        base_model_name = model_name[:-3] if model_name.endswith("_mm") else model_name
        
        if not (source_name in self.source_mapping and base_model_name in self.source_mapping[source_name]):
            return None
            
        # 如果模型映射值为None且是多模态模型（以_mm结尾）
        if self.source_mapping[source_name][base_model_name] is None and model_name.endswith("_mm"):
            # 多模态模型映射为None表示不支持
            return None
        
        return self.source_mapping[source_name][base_model_name]

    def get_config(self, model_name, mode, input_proportion: int, output_proportion: int):
        """维护两套策略, 一套是以便宜为导向,
        一套是以时间最少为导向的.
        
        Args:
            model_name (str): 模型名称
            mode (str): 模式，可以是"cheap_first"或"fast_first"
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            
        Returns:
            tuple: 包含主源和备用源的配置信息
            
        Raises:
            ValueError: 如果找不到可用的源或配置
            Exception: 其他错误
        """
        self.logger.info(f"获取模型 {model_name} 的配置，模式: {mode}, 输入比例: {input_proportion}, 输出比例: {output_proportion}")

        # 无论以什么为导向, 最大概率能跑通是最重要的.
        # 因为跑不通大概不是发不过去, 而是response收不回来.
        # pre-filling也是照常收费的, 与其二遍返工, 还不如一次做好.
        # 因此无论如何, 都先用成功率作为筛选.
        #
        # 如果当前实例初始化的时候距离当前尝试获取配置的时间已过去超过15min了.
        # 那么就自动刷新当前健康检查状态.

        # ================ 状态维护与入参校验 ================
        
        # 修复bug: 使用total_seconds()而不是seconds
        # 同时检查timestamp字段是否存在
        if (self.healthy and "timestamp" in self.healthy and 
            (datetime.now() - datetime.fromisoformat(self.healthy["timestamp"])).total_seconds() > self.healthy.get("check_timer_span", 15)*60):
            self.logger.info("健康检查数据已过期，正在刷新")
            self.healthy = Harness_localAPI.check_healthy()
        
        # 如果健康数据为空，直接使用预设排名
        if self.is_health_data_empty(model_name):
            self.logger.info(f"健康数据为空，使用预设排名选择模型 {model_name} 的源")
            return self.get_sources_from_ranking(model_name)

        # 验证模式参数
        if mode not in ["cheap_first", "fast_first"]:
            self.logger.warning(f"未知的模式 '{mode}'，使用默认模式 'cheap_first'")
            mode = "cheap_first"
        
        # 验证比例参数 - 修复：只需要比例关系正确即可
        if input_proportion == 0 and output_proportion == 0:
            self.logger.warning(f"输入输出比例都为0，使用默认值 50, 50")
            input_proportion = 50
            output_proportion = 50

        # 处理多模态的情况, 多模态完全默认为等同于常规模型.
        # 只是常规模型的另外一种传参模式.
        real_model_name = model_name
        # 不再转换为base_model_name，直接使用完整的model_name
        
        span_mean_list = []
        global_successProb_list = []
        source_list = []
        
        # 收集匹配的模型数据
        for key in self.healthy["data"]:
            # 直接使用完整的model_name进行匹配
            if model_name == key[1]:
                # 检查是否这个源的这个模型近{TOLERANCE_TIMES}次记录中存在任何一次异常情况.
                source_list.append(key[0])
                # 对于没有这个模型的源, 健康检查的数据为空.
                if not self.healthy["data"][key]:
                    # 保证即使为空的事后, span_mean_list, global_successProb_list, source_list三个数组的长度和内容也是对齐的.
                    span_mean_list.append(np.nan)
                    global_successProb_list.append(np.nan)
                    continue
                # 对于健康检查数据不为空的源下的模型, 计算近期平均响应时间
                recent_data = self.healthy["data"][key][-TOLERANCE_TIMES:]
                # 过滤掉None值（失败的请求）
                valid_times = [t for t in recent_data if t is not None and not np.isnan(t)]
                if valid_times:
                    span_mean_list.append(np.mean(valid_times))
                else:
                    span_mean_list.append(np.nan)
                
                # 修复bug: 改进成功率计算，区分"未测试"和"失败"
                # None表示失败，数值表示成功
                success_count = sum(1 for t in self.healthy["data"][key] if t is not None and not np.isnan(t))
                total_count = len(self.healthy["data"][key])
                if total_count > 0:
                    global_successProb_list.append(success_count / total_count)
                else:
                    global_successProb_list.append(np.nan)

        
        # 处理没有找到匹配模型的情况
        if not source_list:
            self.logger.warning(f"未找到匹配模型 {real_model_name} 的任何源")
            # 使用预设排名
            return self.get_sources_from_ranking(real_model_name)
        
        # 成功率排序
        ranking_successProb = {source_list[int(n)]: r+1 for n, r, g in zip(np.argsort(global_successProb_list)[::-1], range(len(global_successProb_list)), global_successProb_list) if not np.isnan(g)}
        
        # 决定使用哪种排序方式
        if np.all(np.isnan(span_mean_list)):
            # 极端情况1，所有源近期都存在异常情况
            # 如果至少对于该模型, 存在任意源是有成功率的, 则使用全局成功率作为参考.
            if np.any(~np.isnan(np.array(global_successProb_list))):
                pre_ranking = ranking_successProb
            else:
                # 极端情况2, 如果所有源近期都存在异常情况, 且所有源都是不存在有效的成功率统计的. (例如服务刚启动, 亦或是干脆就是网从头炸到尾)
                # 则使用默认排序.
                return self.get_sources_from_ranking(real_model_name)
        else:
            # 如果一切正常, 则使用近期平均执行时间
            pre_ranking = {source_list[int(n)]: r+1 for n, r, s in zip(np.argsort(span_mean_list), range(len(span_mean_list)), span_mean_list) if not np.isnan(s)}
        # 模式处理
        if mode == "cheap_first":
            # 计算价格排名
            price_list = []
            inner_source_list = []
            for source_name in pre_ranking:
                try:
                    # 检查模型是否在源上有效
                    if not self._check_valid_model(source_name, real_model_name):
                        self.logger.warning(f"[cheap_first] 模型 {real_model_name} 在源 {source_name} 上不可用，跳过 (因为不知道价格)")
                        continue
                        
                    source_model_name = self._get_actual_model_name(source_name, real_model_name)
                    
                    # 获取价格
                    if source_name in self.source_price and source_model_name in self.source_price[source_name]:
                        price = self.source_price[source_name][source_model_name]
                        if price is None:
                            # 如果价格为None，给低优先级
                            final_price = 1e8
                        elif isinstance(price, tuple):
                            # 确保价格元组中没有None值
                            if None in price:
                                final_price = 1e8
                            else:
                                final_price = (price[0]*input_proportion + price[1]*output_proportion)/(input_proportion+output_proportion)

                        elif isinstance(price, float):
                            final_price = price
                        else:
                            final_price = 1e8  # 未知价格，给最低优先级
                    else:
                        final_price = 1e8  # 找不到价格信息
                        
                    inner_source_list.append(source_name)
                    price_list.append(final_price)
                except Exception as e:
                    self.logger.warning(f"计算源 {source_name} 的价格时出错: {str(e)}")
            
            # 最少可能只有一个源
            if not inner_source_list:
                self.logger.warning(f"未找到具有有效价格信息的源，使用预设排名")
                return self.get_sources_from_ranking(real_model_name)
            
            # 价格排序
            post_ranking = {inner_source_list[int(n)]: r+1 for n, r, p in zip(np.argsort(price_list), range(len(price_list)), price_list) if not np.isnan(p)}
            
            # 融合排名
            final_ranking = self.get_combinedRanking(pre_ranking, post_ranking, 2/3)
            final_ranking = {key: final_ranking[key] for key in final_ranking if self._check_valid_model(key, real_model_name)}
            # 选择主源和备用源
            inner_list = list(final_ranking.keys())
            if len(inner_list) >= 2:
                # 按融合后的排名排序
                sorted_sources = sorted(inner_list, key=lambda x: final_ranking[x])
                main_source_name = sorted_sources[0]
                backup_source_name = sorted_sources[1]
            else:
                main_source_name = inner_list[0]
                backup_source_name = inner_list[0]
            
        elif mode == "fast_first":
            # 直接使用预处理的排名
            inner_list = list(pre_ranking.keys())
            # 过滤掉不支持该模型的源
            valid_sources = [source for source in inner_list if self._check_valid_model(source, real_model_name)]
            
            if not valid_sources:
                self.logger.warning(f"[fast_first] 预处理排名中没有支持模型 {real_model_name} 的有效源，使用预设排名")
                return self.get_sources_from_ranking(real_model_name)
                
            if len(valid_sources) >= 2:
                main_source_name = valid_sources[0]
                backup_source_name = valid_sources[1]
            else:
                main_source_name = valid_sources[0]
                backup_source_name = valid_sources[0]
        
        # 获取模型名称和API密钥
        try:
            main_source_model_name = self._get_actual_model_name(main_source_name, real_model_name)
            backup_source_model_name = self._get_actual_model_name(backup_source_name, real_model_name)
            
            main_api_key = Harness_localAPI.get_api_key(main_source_name)
            backup_api_key = Harness_localAPI.get_api_key(backup_source_name)
        except Exception as e:
            # 统一错误消息格式，包含"无法获取API密钥"
            raise ValueError(f"无法获取API密钥: {str(e)}")
        
        return main_source_name, main_source_model_name, main_api_key, backup_source_name, backup_source_model_name, backup_api_key

    def select_the_best_fromAbatch(self, model_list, mode="fast_first", input_proportion=60, output_proportion=40):
        """从一批模型中选择帕累托最优的模型
        
        Args:
            model_list (list): 模型名称列表
            mode (str): 选择模式，"fast_first"或"cheap_first"
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            
        Returns:
            tuple: (最优模型名, 源名称, 源模型名, API密钥)
            
        Raises:
            ValueError: 如果没有可用的模型
        """
        self.logger.info(f"从模型列表中选择最优模型: {model_list}")
        
        # 刷新健康数据
        if (self.healthy and "timestamp" in self.healthy and 
            (datetime.now() - datetime.fromisoformat(self.healthy["timestamp"])).total_seconds() > self.healthy.get("check_timer_span", 15)*60):
            self.logger.info("健康检查数据已过期，正在刷新")
            self.healthy = Harness_localAPI.check_healthy()
        
        # 收集每个模型的性能数据
        model_stats = {}
        
        for model_name in model_list:
            # 收集该模型在所有源上的数据
            for key, value in self.healthy["data"].items():
                if len(key) >= 2 and key[1] == model_name and value:
                    source_name = key[0]
                    
                    # 检查模型在该源上是否有效
                    if not self._check_valid_model(source_name, model_name):
                        continue
                    
                    # 计算平均响应时间和成功率
                    valid_times = [t for t in value if t is not None and not np.isnan(t)]
                    if valid_times:
                        avg_time = np.mean(valid_times)
                        success_rate = len(valid_times) / len(value)
                        
                        # 获取价格信息
                        source_model_name = self._get_actual_model_name(source_name, model_name)
                        price = 1e8  # 默认高价格
                        
                        if source_name in self.source_price and source_model_name in self.source_price[source_name]:
                            price_info = self.source_price[source_name][source_model_name]
                            if price_info is not None:
                                if isinstance(price_info, tuple) and None not in price_info:
                                    price = (price_info[0]*input_proportion + price_info[1]*output_proportion)/(input_proportion+output_proportion)
                                elif isinstance(price_info, float):
                                    price = price_info
                        
                        # 存储统计信息
                        key_str = f"{model_name}|{source_name}"
                        model_stats[key_str] = {
                            'model_name': model_name,
                            'source_name': source_name,
                            'source_model_name': source_model_name,
                            'avg_time': avg_time,
                            'success_rate': success_rate,
                            'price': price
                        }
        
        if not model_stats:
            # 如果没有健康数据，使用预设排名选择第一个可用的模型
            self.logger.warning("没有找到有效的健康数据，使用预设排名")
            for model_name in model_list:
                try:
                    result = self.get_sources_from_ranking(model_name)
                    return model_name, result[0], result[1], result[2]
                except:
                    continue
            raise ValueError("没有找到任何可用的模型")
        
        # 找出帕累托前沿
        pareto_models = []
        
        for key1, stats1 in model_stats.items():
            is_dominated = False
            
            # 根据模式选择比较维度
            if mode == "fast_first":
                # 比较速度和成功率
                for key2, stats2 in model_stats.items():
                    if key1 != key2:
                        if (stats2['avg_time'] < stats1['avg_time'] and 
                            stats2['success_rate'] >= stats1['success_rate']):
                            is_dominated = True
                            break
            else:  # cheap_first
                # 比较价格和成功率
                for key2, stats2 in model_stats.items():
                    if key1 != key2:
                        if (stats2['price'] < stats1['price'] and 
                            stats2['success_rate'] >= stats1['success_rate']):
                            is_dominated = True
                            break
            
            if not is_dominated:
                pareto_models.append((key1, stats1))
        
        # 从帕累托前沿中选择最优
        if not pareto_models:
            # 如果没有帕累托模型（理论上不应该发生），选择第一个
            key, stats = list(model_stats.items())[0]
        else:
            # 根据模式选择最优
            if mode == "fast_first":
                # 选择最快的
                pareto_models.sort(key=lambda x: x[1]['avg_time'])
            else:  # cheap_first
                # 选择最便宜的
                pareto_models.sort(key=lambda x: x[1]['price'])
            
            key, stats = pareto_models[0]
        
        # 获取API密钥
        try:
            api_key = Harness_localAPI.get_api_key(stats['source_name'])
        except Exception as e:
            raise ValueError(f"无法获取API密钥: {str(e)}")
        
        self.logger.info(f"选择了最优模型: {stats['model_name']} from {stats['source_name']}")
        
        return stats['model_name'], stats['source_name'], stats['source_model_name'], api_key

if __name__ == "__main__":
    # 测试用例
    import random
    load_balancing = LoadBalancing()
    for model_name in model_list_normal+model_list_thinking+model_list_mm_normal+model_list_mm_thinking:
        proportion_1 = random.randint(0,100)
        proportion_2 = random.randint(0,100)
        print("="*128)
        try:
            result = load_balancing.get_config(model_name, "cheap_first", proportion_1, proportion_2)
            # 不打印API密钥，仅打印源和模型名
            print(f"cheap_first for {model_name}: {result[0]} -> {result[1]}, {result[3]} -> {result[4]}")
        except Exception as e:
            print(f"Error for {model_name}: {str(e)}")
        print("\n")
        # print("fast_first", load_balancing.get_config(model_name, "fast_first", proportion_1, proportion_2))
        # print("="*128)
