from openai import OpenAI
from openai._types import NOT_GIVEN

import sys
from pathlib import Path
# 更正导入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ew_decorator.counting_time import counting_time
from ew_decorator.with_timeout import with_timeout

class OpenaiInfra:
    def __init__(self, base_url, api_key) -> None:
       self.openai = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
       
    # 不使用openai.chat.completions.create自有的timeout方法, 而是进行统一的错误管理.
    # 从入参中捕获timeout参数.
    # 对每个底层接口记录执行时间, 添加到返回值的execution_time字段中.
    #
    @with_timeout(timeout_param='timeout')
    @counting_time
    def get_response(self, messages: list, tools: list, model: str, timeout, stream = False, additional_params={}):
        completion = self.openai.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else NOT_GIVEN,
            stream=stream,
            temperature=additional_params["temperature"] if "temperature" in additional_params else NOT_GIVEN,
            top_p=additional_params["top_p"] if "top_p" in additional_params else NOT_GIVEN,
            max_tokens=additional_params["max_tokens"] if "max_tokens" in additional_params else NOT_GIVEN
        )
        
        if not completion.choices:
            raise Exception(f"API响应格式异常: 缺少choices字段. 响应内容: {completion}")

        return {"content": completion.choices[0].message.content,
                "tool_calls": completion.choices[0].message.tool_calls,
                "prompt_tokens":completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "finish_reason": completion.choices[0].finish_reason,
                "model": model}

if __name__ == "__main__":
    # 示例测试代码 - 请替换为您的真实API密钥
    openai_infra_deepinfra = OpenaiInfra("https://api.deerapi.com/v1", "your-api-key-here")
    
    # 测试代码示例
    # print(openai_infra_deepinfra.get_response([{"role": "user", "content": "Hello"}], [], "gpt-3.5-turbo"))
