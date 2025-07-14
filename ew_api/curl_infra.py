import requests
from typing import Dict

import sys
from pathlib import Path
# 更正导入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ew_decorator.counting_time import counting_time
from ew_decorator.with_timeout import with_timeout


class CurlInfra:
    def __init__(self, base_url, api_key) -> None:
        self.base_url = base_url
        self.api_key = api_key
        
    @with_timeout(timeout_param='timeout')
    @counting_time
    def get_response(self,
        messages: list,
        tools: list,
        model: str,
        timeout,
        stream = False,
        additional_params={}
    ) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        if tools:
            payload["tools"] = tools

        if additional_params:
            payload.update(additional_params)
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        completion = response.json()
        
        # 检查是否包含预期的choices字段
        if "choices" not in completion or not completion["choices"]:
            raise Exception(f"API响应格式异常: 缺少choices字段. 响应内容: {completion}")
        
        # 使用get方法安全地获取字段值，避免KeyError
        message = completion["choices"][0]["message"]
        return {
            "content": message["content"],
            "tool_calls": message.get("tool_calls"),
            "prompt_tokens": completion.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": completion.get("usage", {}).get("completion_tokens", 0),
            "finish_reason": completion["choices"][0]["finish_reason"],
            "model": model
        }

if __name__ == "__main__":
    # 示例测试代码 - 请替换为您的真实API密钥
    curl_infra_deerapi = CurlInfra("https://api.deerapi.com/v1/chat/completions", "your-api-key-here")
    
    # 测试代码示例
    # print(curl_infra_deerapi.get_response([{"role": "user", "content": "Hello"}], [], "gpt-3.5-turbo"))