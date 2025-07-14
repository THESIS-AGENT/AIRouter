try:
    # 作为包导入时使用相对导入
    from .LoadBalancing import LoadBalancing, Harness_localAPI
    from .ew_api.curl_infra import CurlInfra
    from .ew_api.openai_infra import OpenaiInfra
    from .ew_config.source import (
        source_config, 
        source_mapping, 
        model_list_normal, 
        model_list_thinking, 
        model_list_mm_normal, 
        model_list_mm_thinking, 
        model_list_function_calling,
        model_list_doc_normal,
        model_list_embedding,
        model_list_reranker
    )
    from .ew_config.api_keys import pool_mapping
except ImportError:
    # 直接运行脚本时使用绝对导入
    from LoadBalancing import LoadBalancing, Harness_localAPI
    from ew_api.curl_infra import CurlInfra
    from ew_api.openai_infra import OpenaiInfra
    from ew_config.source import (
        source_config, 
        source_mapping, 
        model_list_normal, 
        model_list_thinking, 
        model_list_mm_normal, 
        model_list_mm_thinking, 
        model_list_function_calling,
        model_list_doc_normal,
        model_list_embedding,
        model_list_reranker
    )
    from ew_config.api_keys import pool_mapping

import requests
import re
import os
import hashlib
import json
import time
import uuid
import random
from datetime import datetime
import base64

MAX_RETRY = int(os.environ.get("MAX_RETRY", 3))
SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 5))
API_KEY_MANAGER_URL = os.environ.get("API_KEY_MANAGER_URL", "http://localhost:8002")
API_KEY_MANAGER_NOTICE_ENDPOINT = os.environ.get("API_KEY_MANAGER_NOTICE_ENDPOINT", "/notice_apikey")
API_REQUEST_TIMEOUT = int(os.environ.get("API_REQUEST_TIMEOUT", 5))


# 定义模块导出的公共接口
__all__ = [
    'LLM_Wrapper'
]


def remove_thinking(text):
    """
    Remove thinking chains from text content.
    
    Args:
        text (str): Input text that may contain thinking chains.
        
    Returns:
        str: Text with thinking chains removed.
    
    Example:
        "A<think>B</think>C" -> "AC"
    """
    
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

class LLM_Wrapper:
    @staticmethod
    def _download_image_to_base64(img_url: str, timeout: int = 10) -> str:
        """
        Download an image from URL and convert it to base64.
        
        Args:
            img_url (str): The URL of the image to download
            timeout (int): Request timeout in seconds
            
        Returns:
            str: Base64 encoded image data
            
        Raises:
            Exception: If image download or conversion fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(img_url, timeout=timeout, headers=headers)
            response.raise_for_status()
            
            # Convert to base64
            img_base64 = base64.b64encode(response.content).decode('utf-8')
            return img_base64
            
        except Exception as e:
            raise Exception(f"Failed to download and convert image from {img_url}: {str(e)}")

    @staticmethod
    def _send_api_key_usage(
        api_key: str,
        model_name: str,
        source_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        create_time: datetime,
        finish_time: datetime,
        execution_time: float,
        status: bool,
        request_id: str,
        remark: str = "",
    ) -> bool:
        """Send API key usage information to the API key manager."""
        try:
            usage_data = {
                "request_id": request_id,
                "api_key": api_key,
                "model_name": model_name,
                "source_name": source_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "create_time": create_time.isoformat(),
                "finish_time": finish_time.isoformat(),
                "execution_time": execution_time,
                "status": status,
                "remark": remark,
            }

            response = requests.post(
                f"{API_KEY_MANAGER_URL}{API_KEY_MANAGER_NOTICE_ENDPOINT}", 
                json=usage_data,
                timeout=API_REQUEST_TIMEOUT
            )
            return response.status_code == 201
        except Exception as e:
            # Simplify error message to reduce console noise
            print(f"Failed to send API key usage: {str(e).split('(Caused by')[0]}")
            return False

    @staticmethod
    def _generate_request_id(content: str, finish_time: datetime) -> str:
        """Generate a unique request ID based on content and finish time."""
        input_string = f"{content}{finish_time.isoformat()}"
        return hashlib.md5(input_string.encode("utf-8")).hexdigest()

    @staticmethod
    def _verify_model_mapping(
        main_source_name,
        backup_source_name,
        main_source_model_name,
        backup_source_model_name,
        model_name,
    ):
        """Verify that model mappings are valid and not None"""
        # Check for None values in model names
        if main_source_model_name is None:
            raise ValueError(
                f"Model '{model_name}' is not available on source '{main_source_name}'"
            )

        if backup_source_model_name is None:
            raise ValueError(
                f"Model '{model_name}' is not available on backup source '{backup_source_name}'"
            )

        # Check if model names are mapped correctly to source
        if model_name.endswith("_mm"):
            base_model_name = model_name[:-3]
            if (
                source_mapping[main_source_name].get(base_model_name) is None
                and source_mapping[main_source_name].get(model_name) is None
            ):
                raise ValueError(
                    f"Model '{model_name}' is not properly mapped in source '{main_source_name}'"
                )

            if (
                source_mapping[backup_source_name].get(base_model_name) is None
                and source_mapping[backup_source_name].get(model_name) is None
            ):
                raise ValueError(
                    f"Model '{model_name}' is not properly mapped in backup source '{backup_source_name}'"
                )

    @staticmethod
    def _validate_model_for_generate(model_name):
        """Validate that the model is in the allowed list for generate method"""
        allowed_models = model_list_normal + model_list_thinking
        if model_name not in allowed_models:
            raise ValueError(
                f"Model '{model_name}' is not supported for text generation. "
                f"Allowed models: {allowed_models}"
            )

    @staticmethod
    def _validate_model_for_generate_mm(model_name):
        """Validate that the model is in the allowed list for generate_mm method"""
        allowed_models = model_list_mm_normal + model_list_mm_thinking
        if model_name not in allowed_models:
            raise ValueError(
                f"Model '{model_name}' is not supported for multimodal generation. "
                f"Allowed models: {allowed_models}"
            )

    @staticmethod
    def _validate_model_for_function_calling(model_name):
        """Validate that the model is in the allowed list for function_calling method"""
        if model_name not in model_list_function_calling:
            raise ValueError(
                f"Model '{model_name}' is not supported for function calling. "
                f"Allowed models: {model_list_function_calling}"
            )

    @staticmethod
    def _validate_model_for_generate_doc(model_name):
        """Validate that the model is in the allowed list for generate_doc method"""
        if model_name not in model_list_doc_normal:
            raise ValueError(
                f"Model '{model_name}' is not supported for PDF document processing. "
                f"Allowed models: {model_list_doc_normal}"
            )

    @staticmethod
    def _validate_model_is_google_source(model_name):
        """Validate that the model is available on Google source"""
        if "google" not in source_mapping:
            raise ValueError("Google source is not configured")
        
        google_mapping = source_mapping["google"]
        if model_name not in google_mapping or google_mapping[model_name] is None:
            raise ValueError(
                f"Model '{model_name}' is not available on Google source. "
                f"Available Google models: {[k for k, v in google_mapping.items() if v is not None]}"
            )

    @staticmethod
    def _validate_model_for_embedding(model_name):
        """Validate that the model is in the allowed list for embedding method"""
        if model_name not in model_list_embedding:
            raise ValueError(
                f"Model '{model_name}' is not supported for embedding generation. "
                f"Allowed models: {model_list_embedding}"
            )
    
    @staticmethod
    def _validate_model_for_reranker(model_name):
        """Validate that the model is in the allowed list for reranker method"""
        if model_name not in model_list_reranker:
            raise ValueError(
                f"Model '{model_name}' is not supported for reranking. "
                f"Allowed models: {model_list_reranker}"
            )

    @staticmethod
    def _validate_model_is_deepinfra_source(model_name):
        """Validate that the model is available on DeepInfra source"""
        if "deepinfra" not in source_mapping:
            raise ValueError("DeepInfra source is not configured")
        
        deepinfra_mapping = source_mapping["deepinfra"]
        if model_name not in deepinfra_mapping or deepinfra_mapping[model_name] is None:
            raise ValueError(
                f"Model '{model_name}' is not available on DeepInfra source. "
                f"Available DeepInfra models: {[k for k, v in deepinfra_mapping.items() if v is not None]}"
            )

    @staticmethod
    def _build_image_url_with_fallback(img_url, img_base64, source_name=None):
        """
        Build image URL content that supports both formats:
        1. Direct format: "image_url": "url_string"
        2. Nested format: "image_url": {"url": "url_string"}
        
        The order depends on the source provider:
        - DeepInfra prefers direct format (string)
        - OpenAI and Google prefer nested format (object)
        
        Args:
            img_url: Optional image URL
            img_base64: Base64 encoded image
            source_name: Optional source name to determine format preference
            
        Returns:
            tuple: (primary_format, fallback_format)
        """
        url_string = img_url if img_url is not None else f"data:image/jpeg;base64,{img_base64}"
        
        # Direct format (string)
        direct_format = url_string
        
        # Nested format (object)
        nested_format = {"url": url_string}
        
        # Determine format order based on source
        if source_name and source_name.lower() == "deepinfra":
            # DeepInfra prefers direct format
            return direct_format, nested_format
        else:
            # OpenAI, Google, and others prefer nested format
            return nested_format, direct_format

    @staticmethod
    def generate(
        model_name,
        prompt,
        mode="fast_first",
        timeout=30,
        input_proportion=60,
        output_proportion=40,
        max_tokens=None,
        test_response = None,
        remark = ""
    ):
        # Validate model is allowed for text generation
        LLM_Wrapper._validate_model_for_generate(model_name)
        
        if test_response is not None:
            return test_response
        """
        生成文本响应

        Args:
            model_name (str): 模型名称
            prompt (str): 输入提示
            mode (str): 选择策略，"cheap_first"或"fast_first"
            timeout (int): 请求超时时间（秒）
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            max_tokens (int, optional): 最大生成token数，默认None（不限制）

        Returns:
            str: 模型生成的文本

        Raises:
            ValueError: 当模型在源上不可用时
            Exception: 请求失败或其他错误
        """
        try:
            load_balancing = LoadBalancing()
            (
                main_source_name,
                main_source_model_name,
                main_api_key,
                backup_source_name,
                backup_source_model_name,
                backup_api_key,
            ) = load_balancing.get_config(
                model_name, mode, input_proportion, output_proportion
            )
            
            # Verify model mappings are valid
            LLM_Wrapper._verify_model_mapping(
                main_source_name,
                backup_source_name,
                main_source_model_name,
                backup_source_model_name,
                model_name,
            )

            main_source_config = source_config[main_source_name]
            backup_source_config = source_config[backup_source_name]

            # 优先为主模型使用openai-api-sdk的连接方式
            if "openai" in main_source_config:
                main_infra = OpenaiInfra(main_source_config["openai"], main_api_key)
            else:
                main_infra = CurlInfra(main_source_config["curl"], main_api_key)

            # 优先为备用模型使用网络请求curl的连接方式
            if "curl" in backup_source_config:
                backup_infra = CurlInfra(backup_source_config["curl"], backup_api_key)
            else:
                backup_infra = OpenaiInfra(
                    backup_source_config["openai"], backup_api_key
                )

            messages = [{"role": "user", "content": prompt}]
            
            # 只有当max_tokens不为None时才添加到additional_params
            additional_params = {}
            if max_tokens is not None:
                additional_params["max_tokens"] = max_tokens

            curr_retry = 0
            success = False
            create_time = datetime.now()
            content = ""
            used_api_key = main_api_key
            used_model_name = main_source_model_name
            used_source_name = main_source_name
            prompt_tokens = 0
            completion_tokens = 0

            while curr_retry < MAX_RETRY:
                try:
                    # 先尝试主模型
                    response = main_infra.get_response(
                        messages, [], main_source_model_name, timeout=timeout, additional_params=additional_params
                    )
                    used_api_key = main_api_key
                    used_model_name = main_source_model_name
                    used_source_name = main_source_name
                    success = True
                    content = response["content"]
                    prompt_tokens = len(prompt)
                    completion_tokens = len(content)
                    break
                except Exception as e:
                    # 如果主模型失败，尝试备用模型
                    try:
                        response = backup_infra.get_response(
                            messages, [], backup_source_model_name, timeout=timeout, additional_params=additional_params
                        )
                        used_api_key = backup_api_key
                        used_model_name = backup_source_model_name
                        used_source_name = backup_source_name
                        success = True
                        content = response["content"]
                        prompt_tokens = len(prompt)
                        completion_tokens = len(content)
                        break
                    except Exception as backup_e:
                        curr_retry += 1
                        print(
                            f"Retry {curr_retry}/{MAX_RETRY}. Main error: {str(e)}, Backup error: {str(backup_e)}"
                        )
                time.sleep(SLEEP_TIME)
                
            # 记录结束时间和执行时间
            finish_time = datetime.now()
            execution_time = (finish_time - create_time).total_seconds()

            # 生成请求ID
            request_id = LLM_Wrapper._generate_request_id(content, finish_time)

            # 发送API使用记录
            LLM_Wrapper._send_api_key_usage(
                api_key=used_api_key,
                model_name=used_model_name,
                source_name=used_source_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                create_time=create_time,
                finish_time=finish_time,
                execution_time=execution_time,
                status=success,
                request_id=request_id,
                remark=remark
            )

            if not success:
                raise Exception(f"Failed to get response after {MAX_RETRY} retries")

            return remove_thinking(content)
        except ValueError as ve:
            # 重新抛出ValueError，表示模型不可用
            raise ve

    @staticmethod
    def generate_mm(
        model_name: str,
        prompt: str,
        img_base64: str,
        img_url = None,
        timeout=30,
        mode="fast_first",
        input_proportion=60,
        output_proportion=40,
        max_tokens=None,
        test_response = None,
        remark = ""
    ):
        # Validate model is allowed for multimodal generation
        LLM_Wrapper._validate_model_for_generate_mm(model_name)
        
        if test_response is not None:
            return test_response
        """
        使用多模态模型生成响应

        Args:
            model_name (str): 模型名称
            prompt (str): 文本提示
            img_base64 (str): Base64编码的图像
            timeout (int): 请求超时时间（秒）
            mode (str): 选择策略，"cheap_first"或"fast_first"
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            max_tokens (int, optional): 最大生成token数，默认None（不限制）

        Returns:
            str: 模型生成的文本

        Raises:
            ValueError: 当模型在源上不可用时
            Exception: 请求失败或其他错误
        """
        try:
            
            load_balancing = LoadBalancing()
            (
                main_source_name,
                main_source_model_name,
                main_api_key,
                backup_source_name,
                backup_source_model_name,
                backup_api_key,
            ) = load_balancing.get_config(
                model_name, mode, input_proportion, output_proportion
            )

            # Verify model mappings are valid
            LLM_Wrapper._verify_model_mapping(
                main_source_name,
                backup_source_name,
                main_source_model_name,
                backup_source_model_name,
                model_name,
            )

            main_source_config = source_config[main_source_name]
            backup_source_config = source_config[backup_source_name]

            # 优先为主模型使用openai-api-sdk的连接方式
            if "openai" in main_source_config:
                main_infra = OpenaiInfra(main_source_config["openai"], main_api_key)
            else:
                main_infra = CurlInfra(main_source_config["curl"], main_api_key)

            # 优先为备用模型使用网络请求curl的连接方式
            if "curl" in backup_source_config:
                backup_infra = CurlInfra(backup_source_config["curl"], backup_api_key)
            else:
                backup_infra = OpenaiInfra(
                    backup_source_config["openai"], backup_api_key
                )

            # Handle Google API's requirement for base64 images instead of URLs
            # Pre-download image if either main or backup source is Google and we only have URL
            downloaded_img_base64 = img_base64
            
            # Check if we need to download for either Google source
            needs_download = (img_url and not img_base64 and 
                             (main_source_name == "google" or backup_source_name == "google"))
            
            if needs_download:
                try:
                    downloaded_img_base64 = LLM_Wrapper._download_image_to_base64(img_url)
                    print(f"Pre-downloaded image for Google API compatibility")
                except Exception as e:
                    print(f"Warning: Failed to download image for Google API: {str(e)}")
                    # Continue with original img_url, backup source might work
            
            # Set final images for main source
            if main_source_name == "google" and img_url and not img_base64:
                final_img_base64 = downloaded_img_base64
                final_img_url = None if downloaded_img_base64 else img_url
            else:
                final_img_base64 = img_base64
                final_img_url = img_url
            
            # 获取两种图像URL格式
            primary_image_url, fallback_image_url = LLM_Wrapper._build_image_url_with_fallback(final_img_url, final_img_base64, main_source_name)
            
            # 构建多模态消息（使用主格式）
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": primary_image_url,
                        },
                    ],
                }
            ]
            
            # 构建备用格式的消息
            messages_fallback = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": fallback_image_url,
                        },
                    ],
                }
            ]
            
            # 只有当max_tokens不为None时才添加到additional_params
            additional_params = {}
            if max_tokens is not None:
                additional_params["max_tokens"] = max_tokens

            curr_retry = 0
            success = False
            create_time = datetime.now()
            content = ""
            used_api_key = main_api_key
            used_model_name = main_source_model_name
            used_source_name = main_source_name
            prompt_tokens = 0
            completion_tokens = 0

            while curr_retry < MAX_RETRY:
                try:
                    # 先尝试主格式
                    response = main_infra.get_response(
                        messages, [], main_source_model_name, timeout=timeout, additional_params=additional_params
                    )
                    used_api_key = main_api_key
                    used_model_name = main_source_model_name
                    used_source_name = main_source_name
                    success = True
                    
                    # 检查响应完整性，避免隐性超时
                    if response and "content" in response and response["content"]:
                        content = response["content"]
                        prompt_tokens = len(prompt) + len(img_base64)
                        completion_tokens = len(content)
                    else:
                        # 响应为空或不完整，视为隐性超时
                        raise Exception("Empty or incomplete response - possible timeout")
                    break
                except Exception as e:
                    # 如果主格式失败，尝试备用格式
                    try:
                        response = main_infra.get_response(
                            messages_fallback, [], main_source_model_name, timeout=timeout, additional_params=additional_params
                        )
                        used_api_key = main_api_key
                        used_model_name = main_source_model_name
                        used_source_name = main_source_name
                        success = True
                        
                        # 检查响应完整性，避免隐性超时
                        if response and "content" in response and response["content"]:
                            content = response["content"]
                            prompt_tokens = len(prompt) + len(img_base64)
                            completion_tokens = len(content)
                        else:
                            # 响应为空或不完整，视为隐性超时
                            raise Exception("Empty or incomplete response - possible timeout")
                        break
                    except Exception as e2:
                        # 如果主模型的两种格式都失败，尝试备用模型
                        # Handle backup source image format (reuse downloaded image if available)
                        if backup_source_name == "google" and img_url and not img_base64:
                            # Use pre-downloaded image if available
                            backup_final_img_base64 = downloaded_img_base64
                            backup_final_img_url = None if downloaded_img_base64 else img_url
                        else:
                            backup_final_img_base64 = img_base64
                            backup_final_img_url = img_url
                        
                        # 为备用模型重新生成格式
                        backup_primary_image_url, backup_fallback_image_url = LLM_Wrapper._build_image_url_with_fallback(
                            backup_final_img_url, backup_final_img_base64, backup_source_name
                        )
                        
                        # 构建备用模型的消息
                        backup_messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": backup_primary_image_url,
                                    },
                                ],
                            }
                        ]
                        
                        backup_messages_fallback = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": backup_fallback_image_url,
                                    },
                                ],
                            }
                        ]
                        
                        try:
                            response = backup_infra.get_response(
                                    backup_messages, [], backup_source_model_name, timeout=timeout, additional_params=additional_params
                            )
                            used_api_key = backup_api_key
                            used_model_name = backup_source_model_name
                            used_source_name = backup_source_name
                            success = True
                            
                            # 检查响应完整性，避免隐性超时
                            if response and "content" in response and response["content"]:
                                content = response["content"]
                                prompt_tokens = len(prompt) + len(img_base64)
                                completion_tokens = len(content)
                            else:
                                # 响应为空或不完整，视为隐性超时
                                raise Exception("Empty or incomplete response - possible timeout")
                            break
                        except Exception as e3:
                            # 最后尝试备用模型的备用格式
                            try:
                                response = backup_infra.get_response(
                                    backup_messages_fallback, [], backup_source_model_name, timeout=timeout, additional_params=additional_params
                                )
                                used_api_key = backup_api_key
                                used_model_name = backup_source_model_name
                                used_source_name = backup_source_name
                                success = True
                                
                                # 检查响应完整性，避免隐性超时
                                if response and "content" in response and response["content"]:
                                    content = response["content"]
                                    prompt_tokens = len(prompt) + len(img_base64)
                                    completion_tokens = len(content)
                                else:
                                    # 响应为空或不完整，视为隐性超时
                                    raise Exception("Empty or incomplete response - possible timeout")
                                break
                            except Exception as e4:
                                curr_retry += 1
                                print(
                                    f"Retry {curr_retry}/{MAX_RETRY}. All attempts failed: "
                                    f"Main primary: {str(e)}, Main fallback: {str(e2)}, "
                                    f"Backup primary: {str(e3)}, Backup fallback: {str(e4)}"
                                )
                time.sleep(SLEEP_TIME)
                
            # 记录结束时间和执行时间
            finish_time = datetime.now()
            execution_time = (finish_time - create_time).total_seconds()

            # 生成请求ID
            request_id = LLM_Wrapper._generate_request_id(content, finish_time)

            # 发送API使用记录
            LLM_Wrapper._send_api_key_usage(
                api_key=used_api_key,
                model_name=used_model_name,
                source_name=used_source_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                create_time=create_time,
                finish_time=finish_time,
                execution_time=execution_time,
                status=success,
                request_id=request_id,
                remark=remark
            )

            if not success:
                raise Exception(f"Failed to get response after {MAX_RETRY} retries")

            return remove_thinking(content)
        except ValueError as ve:
            # 重新抛出ValueError，表示模型不可用
            raise ve

    @staticmethod
    def function_calling(
        model_name,
        prompt,
        tools,
        timeout=30,
        mode="fast_first",
        input_proportion=60,
        output_proportion=40,
        max_tokens=None,
        test_response = None,
        remark = ""
    ):
        # Validate model is allowed for function calling
        LLM_Wrapper._validate_model_for_function_calling(model_name)
        
        if test_response is not None:
            return test_response
        """
        使用功能调用能力生成响应

        Args:
            model_name (str): 模型名称
            prompt (str): 输入提示
            tools (list): 工具定义列表
            timeout (int): 请求超时时间（秒）
            mode (str): 选择策略，"cheap_first"或"fast_first"
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            max_tokens (int, optional): 最大生成token数，默认None（不限制）

        Returns:
            dict: 包含响应内容和工具调用的完整响应

        Raises:
            ValueError: 当模型在源上不可用时
            Exception: 请求失败或其他错误
        """
        try:
            
            load_balancing = LoadBalancing()
            (
                main_source_name,
                main_source_model_name,
                main_api_key,
                backup_source_name,
                backup_source_model_name,
                backup_api_key,
            ) = load_balancing.get_config(
                model_name, mode, input_proportion, output_proportion
            )

            # Verify model mappings are valid
            LLM_Wrapper._verify_model_mapping(
                main_source_name,
                backup_source_name,
                main_source_model_name,
                backup_source_model_name,
                model_name,
            )

            main_source_config = source_config[main_source_name]
            backup_source_config = source_config[backup_source_name]

            # 优先为主模型使用openai-api-sdk的连接方式
            if "openai" in main_source_config:
                main_infra = OpenaiInfra(main_source_config["openai"], main_api_key)
            else:
                main_infra = CurlInfra(main_source_config["curl"], main_api_key)

            # 优先为备用模型使用网络请求curl的连接方式
            if "curl" in backup_source_config:
                backup_infra = CurlInfra(backup_source_config["curl"], backup_api_key)
            else:
                backup_infra = OpenaiInfra(
                    backup_source_config["openai"], backup_api_key
                )

            messages = [{"role": "user", "content": prompt}]
            
            # 只有当max_tokens不为None时才添加到additional_params
            additional_params = {}
            if max_tokens is not None:
                additional_params["max_tokens"] = max_tokens

            curr_retry = 0
            success = False
            create_time = datetime.now()
            response_content = {}
            used_api_key = main_api_key
            used_model_name = main_source_model_name
            used_source_name = main_source_name
            prompt_tokens = 0
            completion_tokens = 0
            tools_str = json.dumps(tools, ensure_ascii=False)
            
            while curr_retry < MAX_RETRY:
                try:
                    # 先尝试主模型
                    response = main_infra.get_response(
                        messages, tools, main_source_model_name, timeout=timeout, additional_params=additional_params
                    )
                    used_api_key = main_api_key
                    used_model_name = main_source_model_name
                    used_source_name = main_source_name
                    success = True
                    # 对于function calling，保留完整响应以获取工具调用
                    response_content = response
                    prompt_tokens = len(prompt) + len(tools_str)
                    completion_tokens = len(response.get("content", "")) if "content" in response else 0
                    break
                except Exception as e:
                    # 如果主模型失败，尝试备用模型
                    try:
                        response = backup_infra.get_response(
                            messages, tools, backup_source_model_name, timeout=timeout, additional_params=additional_params
                        )
                        used_api_key = backup_api_key
                        used_model_name = backup_source_model_name
                        used_source_name = backup_source_name
                        success = True
                        # 对于function calling，保留完整响应以获取工具调用
                        response_content = response
                        prompt_tokens = len(prompt) + len(tools_str)
                        completion_tokens = len(response.get("content", "")) if "content" in response else 0
                        break
                    except Exception as backup_e:
                        curr_retry += 1
                        print(
                            f"Retry {curr_retry}/{MAX_RETRY}. Main error: {str(e)}, Backup error: {str(backup_e)}"
                        )
                time.sleep(SLEEP_TIME)
                
            # 记录结束时间和执行时间
            finish_time = datetime.now()
            execution_time = (finish_time - create_time).total_seconds()

            # 创建可序列化的响应内容用于生成request_id
            serializable_content = {}
            if "content" in response_content:
                serializable_content["content"] = response_content["content"]

            # 对工具调用进行特殊处理, 避免序列化错误
            if "tool_calls" in response_content:
                serializable_tool_calls = []
                for tool_call in response_content["tool_calls"]:
                    if hasattr(tool_call, "to_dict"):  # 如果是对象而不是dict
                        serializable_tool_calls.append(tool_call.to_dict())
                    elif isinstance(tool_call, dict):  # 如果已经是dict
                        serializable_tool_calls.append(tool_call)
                    else:  # 如果是其他类型的对象
                        serializable_tool_calls.append(
                            {
                                "id": getattr(tool_call, "id", str(uuid.uuid4())),
                                "type": getattr(tool_call, "type", "function"),
                                "function": {
                                    "name": getattr(
                                        getattr(tool_call, "function", {}),
                                        "name",
                                        "unknown",
                                    ),
                                    "arguments": getattr(
                                        getattr(tool_call, "function", {}),
                                        "arguments",
                                        "{}",
                                    ),
                                },
                            }
                        )
                serializable_content["tool_calls"] = serializable_tool_calls

            # 生成请求ID (使用可序列化的内容)
            try:
                request_id = LLM_Wrapper._generate_request_id(
                    json.dumps(serializable_content), finish_time
                )
            except Exception as e:
                print(f"Error generating request_id: {str(e)}")
                request_id = LLM_Wrapper._generate_request_id(
                    f"function_call_{finish_time.isoformat()}", finish_time
                )

            # 发送API使用记录
            LLM_Wrapper._send_api_key_usage(
                api_key=used_api_key,
                model_name=used_model_name,
                source_name=used_source_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                create_time=create_time,
                finish_time=finish_time,
                execution_time=execution_time,
                status=success,
                request_id=request_id,
                remark=remark
            )

            if not success:
                raise Exception(f"Failed to get response after {MAX_RETRY} retries")

            return response_content
        except ValueError as ve:
            # 重新抛出ValueError，表示模型不可用
            raise ve

    @staticmethod
    def generate_fromTHEbest(
        model_list,
        prompt,
        mode="fast_first",
        timeout=30,
        input_proportion=60,
        output_proportion=40,
        max_tokens=None,
        test_response=None,
        remark=""
    ):
        """从多个模型中选择最优的一个进行文本生成
        
        Args:
            model_list (list): 候选模型名称列表
            prompt (str): 输入提示
            mode (str): 选择策略，"cheap_first"或"fast_first"
            timeout (int): 请求超时时间（秒）
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            max_tokens (int, optional): 最大生成token数，默认None（不限制）
            test_response: 测试响应（用于单元测试）
            
        Returns:
            str: 模型生成的文本
            
        Raises:
            ValueError: 当没有可用模型时
            Exception: 请求失败或其他错误
        """
        # 验证所有模型都支持文本生成
        for model_name in model_list:
            LLM_Wrapper._validate_model_for_generate(model_name)
        
        if test_response is not None:
            return test_response
            
        try:
            load_balancing = LoadBalancing()
            
            # 从批量模型中选择最优的
            best_model_name, source_name, source_model_name, api_key = load_balancing.select_the_best_fromAbatch(
                model_list, mode, input_proportion, output_proportion
            )
            
            # 获取源配置
            source_config_item = source_config[source_name]
            
            # 选择合适的基础设施
            if "openai" in source_config_item:
                infra = OpenaiInfra(source_config_item["openai"], api_key)
            else:
                infra = CurlInfra(source_config_item["curl"], api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            # 只有当max_tokens不为None时才添加到additional_params
            additional_params = {}
            if max_tokens is not None:
                additional_params["max_tokens"] = max_tokens
            
            # 记录开始时间
            create_time = datetime.now()
            
            try:
                response = infra.get_response(messages, [], source_model_name, timeout=timeout, additional_params=additional_params)
                success = True
                content = response["content"]
                prompt_tokens = len(prompt)
                completion_tokens = len(content)
            except Exception as e:
                success = False
                content = ""
                prompt_tokens = len(prompt)
                completion_tokens = 0
                raise Exception(f"Failed to get response from {best_model_name}: {str(e)}")
            finally:
                # 记录结束时间
                finish_time = datetime.now()
                execution_time = (finish_time - create_time).total_seconds()
                
                # 生成请求ID
                request_id = LLM_Wrapper._generate_request_id(content, finish_time)
                
                # 发送API使用记录
                LLM_Wrapper._send_api_key_usage(
                    api_key=api_key,
                    model_name=source_model_name,
                    source_name=source_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    create_time=create_time,
                    finish_time=finish_time,
                    execution_time=execution_time,
                    status=success,
                    request_id=request_id,
                remark=remark
            )
            
            return remove_thinking(content)
        except ValueError as ve:
            raise ve

    @staticmethod
    def generate_mm_fromTHEbest(
        model_list,
        prompt,
        img_base64,
        img_url=None,
        timeout=30,
        mode="fast_first",
        input_proportion=60,
        output_proportion=40,
        max_tokens=None,
        test_response=None,
        remark=""
    ):
        """从多个多模态模型中选择最优的一个进行生成
        
        Args:
            model_list (list): 候选多模态模型名称列表
            prompt (str): 文本提示
            img_base64 (str): Base64编码的图像
            img_url (str): 图像URL（可选）
            timeout (int): 请求超时时间（秒）
            mode (str): 选择策略，"cheap_first"或"fast_first"
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            max_tokens (int, optional): 最大生成token数，默认None（不限制）
            test_response: 测试响应（用于单元测试）
            
        Returns:
            str: 模型生成的文本
            
        Raises:
            ValueError: 当没有可用模型时
            Exception: 请求失败或其他错误
        """
        # 验证所有模型都支持多模态生成
        for model_name in model_list:
            LLM_Wrapper._validate_model_for_generate_mm(model_name)
        
        if test_response is not None:
            return test_response
            
        try:
            load_balancing = LoadBalancing()
            
            # 从批量模型中选择最优的
            best_model_name, source_name, source_model_name, api_key = load_balancing.select_the_best_fromAbatch(
                model_list, mode, input_proportion, output_proportion
            )
            
            # 获取源配置
            source_config_item = source_config[source_name]
            
            # 选择合适的基础设施
            if "openai" in source_config_item:
                infra = OpenaiInfra(source_config_item["openai"], api_key)
            else:
                infra = CurlInfra(source_config_item["curl"], api_key)
            
            # 获取两种图像URL格式
            primary_image_url, fallback_image_url = LLM_Wrapper._build_image_url_with_fallback(
                img_url, img_base64, source_name
            )
            
            # 构建多模态消息（使用主格式）
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": primary_image_url,
                        },
                    ],
                }
            ]
            
            # 构建备用格式的消息
            messages_fallback = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": fallback_image_url,
                        },
                    ],
                }
            ]

            # 只有当max_tokens不为None时才添加到additional_params
            additional_params = {}
            if max_tokens is not None:
                additional_params["max_tokens"] = max_tokens
            
            # 记录开始时间
            create_time = datetime.now()
            success = False
            content = ""
            prompt_tokens = len(prompt) + len(img_base64)
            completion_tokens = 0
            
            try:
                # 先尝试主格式
                response = infra.get_response(messages, [], source_model_name, timeout=timeout, additional_params=additional_params)
                success = True
                content = response["content"]
                completion_tokens = len(content)
            except Exception as e:
                # 如果主格式失败，尝试备用格式
                try:
                    response = infra.get_response(messages_fallback, [], source_model_name, timeout=timeout, additional_params=additional_params)
                    success = True
                    content = response["content"]
                    completion_tokens = len(content)
                except Exception as e2:
                    success = False
                    raise Exception(
                        f"Failed to get response from {best_model_name}: "
                        f"Primary format error: {str(e)}, "
                        f"Fallback format error: {str(e2)}"
                    )
            finally:
                # 记录结束时间
                finish_time = datetime.now()
                execution_time = (finish_time - create_time).total_seconds()
                
                # 生成请求ID
                request_id = LLM_Wrapper._generate_request_id(content, finish_time)
                
                # 发送API使用记录
                LLM_Wrapper._send_api_key_usage(
                    api_key=api_key,
                    model_name=source_model_name,
                    source_name=source_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    create_time=create_time,
                    finish_time=finish_time,
                    execution_time=execution_time,
                    status=success,
                    request_id=request_id,
                remark=remark
            )
            
            return remove_thinking(content)
        except ValueError as ve:
            raise ve

    @staticmethod
    def function_calling_fromTHEbest(
        model_list,
        prompt,
        tools,
        timeout=30,
        mode="fast_first",
        input_proportion=60,
        output_proportion=40,
        max_tokens=None,
        test_response=None,
        remark=""
    ):
        """从多个支持函数调用的模型中选择最优的一个
        
        Args:
            model_list (list): 候选模型名称列表（必须支持函数调用）
            prompt (str): 输入提示
            tools (list): 工具定义列表
            timeout (int): 请求超时时间（秒）
            mode (str): 选择策略，"cheap_first"或"fast_first"
            input_proportion (int): 输入比例
            output_proportion (int): 输出比例
            max_tokens (int, optional): 最大生成token数，默认None（不限制）
            test_response: 测试响应（用于单元测试）
            
        Returns:
            dict: 包含响应内容和工具调用的完整响应
            
        Raises:
            ValueError: 当没有可用模型时
            Exception: 请求失败或其他错误
        """
        # 验证所有模型都支持函数调用
        for model_name in model_list:
            LLM_Wrapper._validate_model_for_function_calling(model_name)
        
        if test_response is not None:
            return test_response
            
        try:
            load_balancing = LoadBalancing()
            
            # 从批量模型中选择最优的
            best_model_name, source_name, source_model_name, api_key = load_balancing.select_the_best_fromAbatch(
                model_list, mode, input_proportion, output_proportion
            )
            
            # 获取源配置
            source_config_item = source_config[source_name]
            
            # 选择合适的基础设施
            if "openai" in source_config_item:
                infra = OpenaiInfra(source_config_item["openai"], api_key)
            else:
                infra = CurlInfra(source_config_item["curl"], api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            # 只有当max_tokens不为None时才添加到additional_params
            additional_params = {}
            if max_tokens is not None:
                additional_params["max_tokens"] = max_tokens
            
            # 记录开始时间
            create_time = datetime.now()
            tools_str = json.dumps(tools, ensure_ascii=False)
            
            try:
                response = infra.get_response(messages, tools, source_model_name, timeout=timeout, additional_params=additional_params)
                success = True
                response_content = response
                prompt_tokens = len(prompt) + len(tools_str)
                completion_tokens = len(response.get("content", "")) if "content" in response else 0
            except Exception as e:
                success = False
                response_content = {}
                prompt_tokens = len(prompt) + len(tools_str)
                completion_tokens = 0
                raise Exception(f"Failed to get response from {best_model_name}: {str(e)}")
            finally:
                # 记录结束时间
                finish_time = datetime.now()
                execution_time = (finish_time - create_time).total_seconds()
                
                # 创建可序列化的响应内容用于生成request_id
                serializable_content = {}
                if "content" in response_content:
                    serializable_content["content"] = response_content["content"]

                # 对工具调用进行特殊处理
                if "tool_calls" in response_content:
                    serializable_tool_calls = []
                    for tool_call in response_content["tool_calls"]:
                        if hasattr(tool_call, "to_dict"):
                            serializable_tool_calls.append(tool_call.to_dict())
                        elif isinstance(tool_call, dict):
                            serializable_tool_calls.append(tool_call)
                        else:
                            serializable_tool_calls.append(
                                {
                                    "id": getattr(tool_call, "id", str(uuid.uuid4())),
                                    "type": getattr(tool_call, "type", "function"),
                                    "function": {
                                        "name": getattr(
                                            getattr(tool_call, "function", {}),
                                            "name",
                                            "unknown",
                                        ),
                                        "arguments": getattr(
                                            getattr(tool_call, "function", {}),
                                            "arguments",
                                            "{}",
                                        ),
                                    },
                                }
                            )
                    serializable_content["tool_calls"] = serializable_tool_calls

                # 生成请求ID
                try:
                    request_id = LLM_Wrapper._generate_request_id(
                        json.dumps(serializable_content), finish_time
                    )
                except Exception as e:
                    print(f"Error generating request_id: {str(e)}")
                    request_id = LLM_Wrapper._generate_request_id(
                        f"function_call_{finish_time.isoformat()}", finish_time
                    )
                
                # 发送API使用记录
                LLM_Wrapper._send_api_key_usage(
                    api_key=api_key,
                    model_name=source_model_name,
                    source_name=source_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    create_time=create_time,
                    finish_time=finish_time,
                    execution_time=execution_time,
                    status=success,
                    request_id=request_id,
                remark=remark
            )
            
            return response_content
        except ValueError as ve:
            raise ve

    @staticmethod
    def generate_doc(
        model_name: str,
        prompt: str,
        pdf_base64: str,
        timeout=240,
        test_response=None,
        remark=""
    ):
        """
        使用PDF文档处理模型生成响应（仅支持Google源的模型）
        使用requests直接调用Google的generateContent API

        Args:
            model_name (str): 模型名称（必须是Google源支持的模型）
            prompt (str): 文本提示
            pdf_base64 (str): Base64编码的PDF文档
            timeout (int): 请求超时时间（秒，默认240秒用于大文件处理）
            test_response: 测试响应（用于单元测试）

        Returns:
            str: 模型生成的文本

        Raises:
            ValueError: 当模型不支持PDF处理或不在Google源上时
            Exception: 请求失败或其他错误
        """
        # 验证模型支持PDF文档处理
        LLM_Wrapper._validate_model_for_generate_doc(model_name)
        
        # 验证模型在Google源上可用
        LLM_Wrapper._validate_model_is_google_source(model_name)
        
        if test_response is not None:
            return test_response

        try:
            # 获取Google源配置
            source_name = "google"
            source_model_name = source_mapping[source_name][model_name]
            
            # 获取API密钥
            harness = Harness_localAPI()
            api_key = harness.get_api_key(source_name)
            
            # 记录开始时间
            create_time = datetime.now()
            
            # 构造请求
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{source_model_name}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_base64
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }]
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if "candidates" not in result or len(result["candidates"]) == 0:
                raise Exception(f"No candidates in response")
            
            candidate = result["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise Exception(f"Invalid response structure")
            
            parts = candidate["content"]["parts"]
            if len(parts) == 0 or "text" not in parts[0]:
                raise Exception(f"No text content in response")
            
            content = parts[0]["text"]
            
            # 记录结束时间和使用统计
            finish_time = datetime.now()
            execution_time = (finish_time - create_time).total_seconds()
            request_id = LLM_Wrapper._generate_request_id(content, finish_time)
            
            # 发送API使用记录
            LLM_Wrapper._send_api_key_usage(
                api_key=api_key,
                model_name=source_model_name,
                source_name=source_name,
                prompt_tokens=len(prompt) + len(pdf_base64),
                completion_tokens=len(content),
                create_time=create_time,
                finish_time=finish_time,
                execution_time=execution_time,
                status=True,
                request_id=request_id,
                remark=remark
            )
            
            return remove_thinking(content)
            
        except ValueError as ve:
            # 重新抛出ValueError，表示模型不可用
            raise ve
        except Exception as e:
            # 记录失败的API使用
            try:
                finish_time = datetime.now()
                execution_time = (finish_time - create_time).total_seconds()
                request_id = LLM_Wrapper._generate_request_id("", finish_time)
                
                LLM_Wrapper._send_api_key_usage(
                    api_key=api_key if 'api_key' in locals() else "",
                    model_name=source_model_name if 'source_model_name' in locals() else model_name,
                    source_name=source_name,
                    prompt_tokens=len(prompt) + len(pdf_base64),
                    completion_tokens=0,
                    create_time=create_time if 'create_time' in locals() else datetime.now(),
                    finish_time=finish_time,
                    execution_time=execution_time,
                    status=False,
                    request_id=request_id,
                    remark=remark
                )
            except:
                pass  # 忽略记录失败的错误
            
            raise Exception(f"PDF processing failed: {str(e)}")
    
    @staticmethod
    def generate_embedding(model_name: str,
        prompt: str,
        test_response=None,
        timeout=10,
        remark="embedding"):
        """
        生成文本嵌入向量

        Args:
            model_name (str): 模型名称，仅支持embedding模型
            prompt (str): 输入文本
            test_response (dict, optional): 测试响应，用于测试
            timeout (int): 请求超时时间（秒）
            remark (str): 备注信息

        Returns:
            dict: 包含嵌入向量和使用信息的响应

        Raises:
            ValueError: 当模型不支持或不可用时
            Exception: 请求失败或其他错误
        """
        # 验证模型是否支持embedding
        LLM_Wrapper._validate_model_for_embedding(model_name)
        
        if test_response is not None:
            return test_response
            
        # 只支持deepinfra源
        source_name = "deepinfra"
        deepinfra_config = source_config[source_name]
        
        # 获取实际模型名称
        actual_model_name = model_name  # embedding模型使用原始名称
        
        # 获取API密钥
        harness = Harness_localAPI()
        api_key = harness.get_api_key(source_name)
        
        # 创建CurlInfra实例
        curl_infra = CurlInfra("https://api.deepinfra.com/v1/openai/embeddings", api_key)
        
        curr_retry = 0
        success = False
        create_time = datetime.now()
        embedding_result = None
        prompt_tokens = 0
        completion_tokens = 0
        
        while curr_retry < MAX_RETRY:
            try:
                # 构建请求数据
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                payload = {
                    "input": prompt,
                    "model": actual_model_name,
                    "encoding_format": "float"
                }
                
                # 发送请求
                response = requests.post(
                    "https://api.deepinfra.com/v1/openai/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                
                # 解析响应
                response_data = response.json()
                
                # 检查响应格式
                if "data" not in response_data or not response_data["data"]:
                    raise Exception(f"API响应格式异常: 缺少data字段. 响应内容: {response_data}")
                
                # 提取嵌入向量
                embedding_result = {
                    "embedding": response_data["data"][0]["embedding"],
                    "model": response_data["model"],
                    "usage": response_data.get("usage", {})
                }
                
                prompt_tokens = response_data.get("usage", {}).get("prompt_tokens", len(prompt.split()))
                completion_tokens = 0  # embedding不产生completion tokens
                success = True
                break
                
            except Exception as e:
                curr_retry += 1
                if curr_retry < MAX_RETRY:
                    print(f"Embedding retry {curr_retry}/{MAX_RETRY}. Error: {str(e)}")
                    time.sleep(SLEEP_TIME)
                else:
                    print(f"Embedding failed after {MAX_RETRY} retries. Final error: {str(e)}")
                    
        # 记录结束时间和执行时间
        finish_time = datetime.now()
        execution_time = (finish_time - create_time).total_seconds()
        
        # 生成请求ID
        request_id = LLM_Wrapper._generate_request_id(str(embedding_result), finish_time)
        
        # 发送API使用记录
        LLM_Wrapper._send_api_key_usage(
            api_key=api_key,
            model_name=actual_model_name,
            source_name=source_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            create_time=create_time,
            finish_time=finish_time,
            execution_time=execution_time,
            status=success,
            request_id=request_id,
            remark=remark
        )
        
        if not success:
            raise Exception(f"Failed to generate embedding after {MAX_RETRY} retries")
            
        return embedding_result
    
    @staticmethod
    def generate_reranker(model_name: str,
        prompt: str,
        documents_list: list,
        timeout=10,
        test_response=None,
        remark="reranker"):
        """
        使用reranker模型对文档进行重新排序

        Args:
            model_name (str): 模型名称，仅支持reranker模型
            prompt (str): 查询文本
            documents_list (list): 文档列表
            timeout (int): 请求超时时间（秒）
            test_response (dict, optional): 测试响应，用于测试
            remark (str): 备注信息

        Returns:
            dict: 包含重新排序结果的响应

        Raises:
            ValueError: 当模型不支持或不可用时
            Exception: 请求失败或其他错误
        """
        # 验证模型是否支持reranking
        LLM_Wrapper._validate_model_for_reranker(model_name)
        
        if test_response is not None:
            return test_response
            
        # 验证输入参数
        if not isinstance(documents_list, list) or len(documents_list) == 0:
            raise ValueError("documents_list must be a non-empty list")
            
        # 只支持deepinfra源
        source_name = "deepinfra"
        deepinfra_config = source_config[source_name]
        
        # 获取实际模型名称
        actual_model_name = model_name  # reranker模型使用原始名称
        
        # 获取API密钥
        harness = Harness_localAPI()
        api_key = harness.get_api_key(source_name)
        
        curr_retry = 0
        success = False
        create_time = datetime.now()
        reranker_result = None
        prompt_tokens = 0
        completion_tokens = 0
        
        while curr_retry < MAX_RETRY:
            try:
                # 构建请求数据
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"bearer {api_key}"
                }
                
                payload = {
                    "queries": [prompt] * len(documents_list),
                    "documents": documents_list
                }
                
                # 发送请求
                response = requests.post(
                    f"https://api.deepinfra.com/v1/inference/{actual_model_name}",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                
                # 解析响应
                response_data = response.json()
                
                # 检查响应格式
                if "scores" not in response_data:
                    raise Exception(f"API响应格式异常: 缺少scores字段. 响应内容: {response_data}")
                
                # 提取重新排序结果
                reranker_result = {
                    "scores": response_data["scores"],
                    "input_tokens": response_data.get("input_tokens", 0),
                    "request_id": response_data.get("request_id"),
                    "inference_status": response_data.get("inference_status", {})
                }
                
                prompt_tokens = response_data.get("input_tokens", len(prompt.split()) + sum(len(doc.split()) for doc in documents_list))
                completion_tokens = 0  # reranker不产生completion tokens
                success = True
                break
                
            except Exception as e:
                curr_retry += 1
                if curr_retry < MAX_RETRY:
                    print(f"Reranker retry {curr_retry}/{MAX_RETRY}. Error: {str(e)}")
                    time.sleep(SLEEP_TIME)
                else:
                    print(f"Reranker failed after {MAX_RETRY} retries. Final error: {str(e)}")
                    
        # 记录结束时间和执行时间
        finish_time = datetime.now()
        execution_time = (finish_time - create_time).total_seconds()
        
        # 生成请求ID
        request_id = LLM_Wrapper._generate_request_id(str(reranker_result), finish_time)
        
        # 发送API使用记录
        LLM_Wrapper._send_api_key_usage(
            api_key=api_key,
            model_name=actual_model_name,
            source_name=source_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            create_time=create_time,
            finish_time=finish_time,
            execution_time=execution_time,
            status=success,
            request_id=request_id,
            remark=remark
        )
        
        if not success:
            raise Exception(f"Failed to rerank documents after {MAX_RETRY} retries")
            
        return reranker_result
    
if __name__ == "__main__":
    # # 测试embedding功能
    # print("Testing generate_embedding...")
    # try:
    #     embedding_result = LLM_Wrapper.generate_embedding(
    #         "Qwen/Qwen3-Embedding-4B",
    #         "The food was delicious and the waiter was very friendly.",
    #         timeout=30,
    #         remark="test_embedding"
    #     )
    #     print(f"Embedding generation success!")
    #     print(f"Embedding dimensions: {len(embedding_result['embedding'])}")
    #     print(f"Usage: {embedding_result['usage']}")
    #     print(f"Model: {embedding_result['model']}")
    # except Exception as e:
    #     print(f"Embedding test failed: {e}")
    
    # print("\n" + "="*50 + "\n")
    
    # # 测试reranker功能
    # print("Testing generate_reranker...")
    # try:
    #     reranker_result = LLM_Wrapper.generate_reranker(
    #         "Qwen/Qwen3-Reranker-4B",
    #         "What is the capital of United States of America?",
    #         [
    #             "The capital of USA is Washington DC.",
    #             "New York is the largest city in the United States.",
    #             "The United States has 50 states.",
    #             "Washington DC is located on the East Coast.",
    #             "The US capital was established in 1790."
    #         ],
    #         timeout=30,
    #         remark="test_reranker"
    #     )
    #     print(f"Reranker success!")
    #     print(f"Scores: {reranker_result['scores']}")
    #     print(f"Input tokens: {reranker_result['input_tokens']}")
    #     print(f"Request ID: {reranker_result['request_id']}")
        
    #     # 显示排序结果
    #     documents = [
    #         "The capital of USA is Washington DC.",
    #         "New York is the largest city in the United States.",
    #         "The United States has 50 states.",
    #         "Washington DC is located on the East Coast.",
    #         "The US capital was established in 1790."
    #     ]
        
    #     # 根据分数排序
    #     scored_docs = list(zip(documents, reranker_result['scores']))
    #     scored_docs.sort(key=lambda x: x[1], reverse=True)
        
    #     print("\nRanked documents:")
    #     for i, (doc, score) in enumerate(scored_docs):
    #         print(f"{i+1}. (Score: {score:.4f}) {doc}")
            
    # except Exception as e:
    #     print(f"Reranker test failed: {e}")
    
    # print("\n" + "="*50 + "\n")
    
    # 使用简单的测试PDF内容进行演示
    print("Testing generate_doc with simple test PDF...")
    test_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n293\n%%EOF'
    pdf_base64 = base64.b64encode(test_pdf_content).decode('utf-8')
    
    print(f"PDF base64 length: {len(pdf_base64)} characters")
    
    try:
        result = LLM_Wrapper.generate_doc(
            "gemini25_flash",
            "请为我将这个pdf转换为html",
            pdf_base64,
            timeout=60,
            remark=""
        )
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 如果想要测试原始大文件，可以取消注释以下代码：
    # print("\nTesting with original large PDF file...")
    # try:
    #     with open("path/to/your/test.pdf", 'rb') as pdf_file:
    #         pdf_content = pdf_file.read()
    #         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
    #     result = LLM_Wrapper.generate_doc("gemini25_flash",
    #         "请为我将这个pdf转换为html",
    #         pdf_base64,
    #         timeout=240)
    #     print(f"Large PDF result: {result[:200]}...")
    # except Exception as e:
    #     print(f"Large PDF test failed: {e}")
    