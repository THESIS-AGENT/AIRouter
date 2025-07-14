import uvicorn

"""
API密钥管理器服务 (APIKeyManager)

该服务在Docker容器内运行，提供全局API密钥负载均衡管理，主要功能包括：

1. 智能分配API密钥：
   - 通过/get_apikey接口提供最佳API密钥选择
   - 采用轮询(round-robin)方式均衡分配负载
   - 自动识别并暂时跳过在最近{TOLERANCE_TIMER_SPAN}分钟内有失败记录的API密钥
   - 即使所有密钥都有失败记录，仍会返回可用密钥，确保服务持续可用

2. 监控和记录API密钥使用情况：
   - 通过/notice_apikey接口接收并记录每次API调用的结果
   - 存储以下关键指标到数据库：
     - api_key: API密钥值 (必填)
     - request_id: 请求唯一标识符 (主键，必填)
     - model_name: 使用的模型名称 (必填)
     - source_name: API提供商/源 (必填)
     - prompt_tokens: 输入token数量 (可选)
     - completion_tokens: 输出token数量 (可选)
     - create_time: 请求开始时间 (必填)
     - finish_time: 请求结束时间 (必填)
     - execution_time: 执行耗时 (必填)
     - status: 请求状态 (True=成功，False=失败) (必填)

数据库表结构已在models.py中通过SQLAlchemy ORM实现，支持MySQL数据库存储。
客户端库(client.py)提供简便的接口调用方法，方便其他服务集成使用。
"""
        
if __name__ == "__main__":
    # 运行API密钥管理器服务
    uvicorn.run("api_key_manager.api:app", host="0.0.0.0", port=8000, reload=True, log_level="error") 