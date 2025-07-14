from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ApiKeyRequest(BaseModel):
    """请求特定源的API密钥的模式。"""
    source_name: str = Field(..., description="API源的名称")


class ApiKeyUsageCreate(BaseModel):
    """创建新的API密钥使用记录的模式。"""
    request_id: str = Field(..., description="此请求的唯一标识符")
    api_key: str = Field(..., description="请求中使用的API密钥")
    model_name: str = Field(..., description="使用的模型名称")
    source_name: str = Field(..., description="接口供应商名称")
    prompt_tokens: Optional[int] = Field(None, description="输入令牌数量")
    completion_tokens: Optional[int] = Field(None, description="输出令牌数量")
    create_time: datetime = Field(..., description="请求开始时间")
    finish_time: datetime = Field(..., description="请求完成时间")
    execution_time: float = Field(..., description="总执行时间（秒）")
    status: bool = Field(..., description="请求是否成功")
    remark: Optional[str] = Field("", description="备注信息，用于记录API调用的用途或来源")


class ApiKeyResponse(BaseModel):
    """API密钥响应的模式。"""
    api_key: str = Field(..., description="要使用的API密钥") 