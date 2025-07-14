import requests
import uuid
from datetime import datetime
from typing import Optional, Union

class APIKeyManagerClient:
    """与API密钥管理器服务交互的客户端。"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        """初始化客户端。
        
        参数:
            base_url: API密钥管理器服务的基础URL
        """
        self.base_url = base_url.rstrip('/')
        
    def get_api_key(self, source_name: str) -> Optional[str]:
        """获取特定源的API密钥。
        
        参数:
            source_name: 接口供应商名称
            
        返回:
            API密钥，如果请求失败则返回None
        """
        try:
            response = requests.post(
                f"{self.base_url}/get_apikey", 
                json={"source_name": source_name},
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("api_key")
            else:
                print(f"获取API密钥失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"获取API密钥时出错: {str(e)}")
            return None
    
    def notice_api_key_usage(
        self, 
        api_key: str, 
        model_name: str, 
        source_name: str, 
        create_time: Union[datetime, str],
        finish_time: Union[datetime, str],
        execution_time: float,
        status: bool,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
        remark: Optional[str] = ""
    ) -> bool:
        """通知服务关于API密钥的使用情况。
        
        参数:
            api_key: 使用的API密钥
            model_name: 模型名称
            source_name: 接口供应商名称
            create_time: 请求开始时间
            finish_time: 请求完成时间
            execution_time: 执行时间（秒）
            status: 请求是否成功
            prompt_tokens: 输入令牌数量（可选）
            completion_tokens: 输出令牌数量（可选）
            request_id: 自定义请求ID（可选，如果未提供将生成UUID）
            remark: 备注信息，用于记录API调用的用途或来源（可选）
            
        返回:
            通知是否成功
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
            
        # 将datetime对象转换为ISO格式字符串
        if isinstance(create_time, datetime):
            create_time = create_time.isoformat()
        if isinstance(finish_time, datetime):
            finish_time = finish_time.isoformat()
            
        # 构建载荷
        payload = {
            "request_id": request_id,
            "api_key": api_key,
            "model_name": model_name,
            "source_name": source_name,
            "create_time": create_time,
            "finish_time": finish_time,
            "execution_time": execution_time,
            "status": status,
            "remark": remark or ""
        }
        
        # 如果提供了可选字段，则添加
        if prompt_tokens is not None:
            payload["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            payload["completion_tokens"] = completion_tokens
            
        try:
            response = requests.post(
                f"{self.base_url}/notice_apikey",
                json=payload,
                timeout=5
            )
            return response.status_code == 201
        except Exception as e:
            print(f"通知API密钥使用情况时出错: {str(e)}")
            return False 