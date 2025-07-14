from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Dict, List, Tuple, Set
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from collections import defaultdict, Counter
import asyncio

# 导入本地模块
from .models import get_db, ApiKeyUsage, create_tables
from .schemas import ApiKeyRequest, ApiKeyUsageCreate, ApiKeyResponse

# 导入配置
import sys
import os
# 添加父目录到路径以导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从正确的配置文件导入所有配置
from ew_config.api_keys import pool_mapping
from ew_config.source import *

# 配置参数
# 不可以忍受最近{TOLERANCE_TIMER_SPAN}分钟内存在任意一次错误记录的api_key.
TOLERANCE_TIMER_SPAN = int(os.environ.get("TOLERANCE_TIMER_SPAN", 15))
# 定时任务间隔：每多少分钟查询一次失败的API密钥，默认1分钟
FAILED_KEY_CHECK_INTERVAL = int(os.environ.get("FAILED_KEY_CHECK_INTERVAL", 1))

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,  # 改为INFO级别以显示汇总报告
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# 减少FastAPI和SQLAlchemy的日志噪音
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.ERROR)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

app = FastAPI(
    title="API Key Manager",
    description="Service for managing API keys with load balancing and failure tracking",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局缓存和状态管理 ====================

# 失败的API密钥缓存：{source_name: {api_key1, api_key2, ...}}
failed_keys_cache: Dict[str, Set[str]] = defaultdict(set)

# API密钥失败次数缓存：{source_name: {api_key: failure_count}}
key_failure_count_cache: Dict[str, Dict[str, int]] = defaultdict(dict)

# 密钥使用索引缓存，用于负载均衡
key_usage_cache: Dict[str, Dict[str, int]] = {}
global_index_cache: Dict[str, int] = {}

# 统计信息缓存
stats_cache: Dict[str, Dict] = {}

# 最后更新时间
last_update_time: datetime = datetime.now()

# ==================== 定时任务函数 ====================

def update_failed_keys_cache():
    """定时任务：更新失败的API密钥缓存"""
    global last_update_time
    start_time = datetime.now()
    logger.info("🔄 开始更新失败API密钥缓存...")
    
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 计算时间窗口
        cutoff_time = datetime.now() - timedelta(minutes=TOLERANCE_TIMER_SPAN)
        
        # 重置缓存
        failed_keys_cache.clear()
        key_failure_count_cache.clear()
        stats_cache.clear()
        
        # 批量查询所有失败的API密钥 - 使用优化的索引查询
        failed_keys_query = db.query(
            ApiKeyUsage.source_name,
            ApiKeyUsage.api_key,
            func.count(ApiKeyUsage.request_id).label('failure_count'),
            func.max(ApiKeyUsage.finish_time).label('last_failure')
        ).filter(
            and_(
                ApiKeyUsage.status == False,
                ApiKeyUsage.finish_time >= cutoff_time
            )
        ).group_by(
            ApiKeyUsage.source_name,
            ApiKeyUsage.api_key
        ).all()
        
        # 统计信息
        total_failed_keys = 0
        source_stats = defaultdict(lambda: {
            'failed_keys': 0,
            'total_failures': 0,
            'models_affected': set(),
            'last_failure': None
        })
        
        # 处理查询结果
        for row in failed_keys_query:
            source_name = row.source_name
            api_key = row.api_key
            failure_count = row.failure_count
            last_failure = row.last_failure
            
            # 添加到失败缓存
            failed_keys_cache[source_name].add(api_key)
            # 记录失败次数
            key_failure_count_cache[source_name][api_key] = failure_count
            total_failed_keys += 1
            
            # 更新统计信息
            source_stats[source_name]['failed_keys'] += 1
            source_stats[source_name]['total_failures'] += failure_count
            if source_stats[source_name]['last_failure'] is None or last_failure > source_stats[source_name]['last_failure']:
                source_stats[source_name]['last_failure'] = last_failure
        
        # 查询受影响的模型统计
        model_stats_query = db.query(
            ApiKeyUsage.source_name,
            ApiKeyUsage.model_name,
            func.count(ApiKeyUsage.request_id).label('failure_count')
        ).filter(
            and_(
                ApiKeyUsage.status == False,
                ApiKeyUsage.finish_time >= cutoff_time
            )
        ).group_by(
            ApiKeyUsage.source_name,
            ApiKeyUsage.model_name
        ).all()
        
        for row in model_stats_query:
            source_stats[row.source_name]['models_affected'].add(row.model_name)
        
        # 保存统计信息
        stats_cache.update(source_stats)
        
        # 关闭数据库会话
        db.close()
        
        # 计算执行时间
        execution_time = (datetime.now() - start_time).total_seconds()
        last_update_time = datetime.now()
        
        # 生成汇总报告
        _generate_failed_keys_summary_report(total_failed_keys, source_stats, execution_time)
        
    except Exception as e:
        logger.error(f"❌ 更新失败API密钥缓存时出错: {str(e)}")
        
def _generate_failed_keys_summary_report(total_failed_keys: int, source_stats: dict, execution_time: float):
    """生成失败密钥的汇总报告"""
    logger.info("📊 ==================== API密钥失败情况汇总报告 ====================")
    logger.info(f"📊 查询执行时间: {execution_time:.2f}s")
    logger.info(f"📊 时间窗口: 最近{TOLERANCE_TIMER_SPAN}分钟")
    logger.info(f"📊 失败密钥总数: {total_failed_keys}")
    
    if not source_stats:
        logger.info("📊 ✅ 所有API密钥运行正常，无失败记录")
        logger.info("📊 ===============================================================")
        return
    
    # 按失败密钥数量排序
    sorted_sources = sorted(source_stats.items(), key=lambda x: x[1]['failed_keys'], reverse=True)
    
    for source_name, stats in sorted_sources:
        logger.info(f"📊 源 [{source_name}]:")
        logger.info(f"📊   - 失败密钥数: {stats['failed_keys']}")
        logger.info(f"📊   - 失败次数: {stats['total_failures']}")
        logger.info(f"📊   - 受影响模型: {len(stats['models_affected'])} 个")
        if stats['models_affected']:
            models_list = ', '.join(list(stats['models_affected'])[:5])  # 只显示前5个
            if len(stats['models_affected']) > 5:
                models_list += f"... (共{len(stats['models_affected'])}个)"
            logger.info(f"📊   - 模型列表: {models_list}")
        if stats['last_failure']:
            logger.info(f"📊   - 最后失败: {stats['last_failure'].strftime('%H:%M:%S')}")
    
    logger.info("📊 ===============================================================")

# ==================== 调度器设置 ====================

scheduler = BackgroundScheduler()

@app.on_event("startup")
async def startup_event():
    """在启动时初始化数据库表和定时任务"""
    try:
        logger.info("🚀 API密钥管理服务正在启动...")
        
        # 检查并初始化数据库表（仅在必要时）
        logger.info("🔧 检查数据库表状态...")
        create_tables()
        logger.info("🔧 数据库表检查完成")
        
        # 初始化缓存
        logger.info("🔧 初始化缓存...")
        # 只初始化有API密钥的源
        for source_name in pool_mapping.keys():
            if source_name not in key_usage_cache:
                key_usage_cache[source_name] = {}
            if source_name not in global_index_cache:
                global_index_cache[source_name] = -1
        
        logger.info(f"🔧 初始化了 {len(pool_mapping)} 个源的缓存: {', '.join(pool_mapping.keys())}")
        
        # 立即执行一次失败密钥更新
        logger.info("🔧 执行初始失败密钥检查...")
        update_failed_keys_cache()
        
        # 启动定时任务
        scheduler.add_job(
            update_failed_keys_cache,
            trigger=IntervalTrigger(minutes=FAILED_KEY_CHECK_INTERVAL),
            id="failed_keys_check_job",
            name=f"Update failed API keys cache every {FAILED_KEY_CHECK_INTERVAL} minutes",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300
        )
        
        scheduler.start()
        logger.info(f"⏰ 定时任务已启动，每{FAILED_KEY_CHECK_INTERVAL}分钟检查一次失败的API密钥")
        logger.info("✅ API密钥管理服务启动完成")
        
    except Exception as e:
        logger.error(f"❌ 初始化API密钥管理服务时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="服务初始化失败")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭定时任务"""
    logger.info("🛑 API密钥管理服务正在关闭...")
    scheduler.shutdown()
    logger.info("✅ 定时任务已关闭")

# ==================== 中间件和健康检查 ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    if request.url.path not in ["/health", "/check_healthy"]:
        logger.debug(f"收到请求: {request.method} {request.url}")
    response = await call_next(request)
    if response.status_code >= 400:
        logger.warning(f"错误响应: {response.status_code} for {request.method} {request.url}")
    elif request.url.path not in ["/health", "/check_healthy"]:
        logger.debug(f"发送响应: {response.status_code}")
    return response

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}

@app.get("/check_healthy", response_model=Dict[str, str])
async def check_healthy():
    """专门用于Docker健康检查的端点"""
    try:
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

# ==================== 核心API端点 ====================

@app.post("/get_apikey", response_model=ApiKeyResponse)
async def get_api_key(request: ApiKeyRequest):
    """
    获取给定源的最佳API密钥。
    使用缓存的失败密钥列表，实现高性能的密钥选择。
    """
    logger.debug(f"请求源 '{request.source_name}' 的API密钥")
    source_name = request.source_name
    
    # 检查源是否存在
    if source_name not in pool_mapping:
        available_sources = list(pool_mapping.keys())
        logger.warning(f"请求不存在的源: '{source_name}' (可用源: {', '.join(available_sources)})")
        raise HTTPException(status_code=404, detail=f"找不到源 '{source_name}'")
    
    # 获取API密钥池
    api_keys_pool = pool_mapping[source_name]
    
    # 初始化缓存（如果需要）
    if source_name not in key_usage_cache:
        key_usage_cache[source_name] = {}
    if source_name not in global_index_cache:
        global_index_cache[source_name] = -1
    
    # 收集所有可用的API密钥
    all_keys: List[Tuple[str, int, str]] = []
    for user_name in api_keys_pool:
        if user_name not in key_usage_cache[source_name]:
            key_usage_cache[source_name][user_name] = -1
            
        for i, element in enumerate(api_keys_pool[user_name]):
            all_keys.append((user_name, i, element["api_key"]))
    
    if not all_keys:
        logger.error(f"源 '{source_name}' 没有可用的API密钥")
        raise HTTPException(status_code=404, detail=f"源 '{source_name}' 没有可用的API密钥")
    
    # 使用缓存的失败密钥列表（无需数据库查询）
    failing_keys = failed_keys_cache.get(source_name, set())
    
    # 首先尝试使用正常工作的密钥
    working_keys = [(idx, user, key_idx, api_key) for idx, (user, key_idx, api_key) in enumerate(all_keys) if api_key not in failing_keys]
    
    if working_keys:
        # 使用轮询方式选择正常工作的密钥
        current_global_index = global_index_cache[source_name]
        next_key_idx = (current_global_index + 1) % len(working_keys)
        global_index_cache[source_name] = next_key_idx
        
        _, user_name, key_index, api_key = working_keys[next_key_idx]
        key_usage_cache[source_name][user_name] = key_index
        
        logger.debug(f"返回API密钥（健康轮询）: {api_key[:8]}...")
        return ApiKeyResponse(api_key=api_key)
    
    # 如果所有密钥都有失败记录，选择失败次数最少的密钥
    cutoff_time = datetime.now() - timedelta(minutes=TOLERANCE_TIMER_SPAN)
    failure_counts = key_failure_count_cache.get(source_name, {})
    
    logger.warning(f"🔍 源 '{source_name}' 所有API密钥都有失败记录 (时间窗口: 最近{TOLERANCE_TIMER_SPAN}分钟)，选择失败次数最少的密钥")
    
    # 计算每个密钥的失败次数，没有记录的视为0次失败
    key_with_failures = []
    for user_name, key_index, api_key in all_keys:
        failure_count = failure_counts.get(api_key, 0)
        key_with_failures.append((failure_count, user_name, key_index, api_key))
    
    # 按失败次数排序，选择失败次数最少的
    key_with_failures.sort(key=lambda x: x[0])
    failure_count, user_name, key_index, api_key = key_with_failures[0]
    
    key_usage_cache[source_name][user_name] = key_index
    
    logger.info(f"🎯 选择失败次数最少的API密钥: {api_key[:8]}... (失败次数: {failure_count})")
    return ApiKeyResponse(api_key=api_key)

@app.post("/notice_apikey", status_code=201)
async def notice_api_key(usage: ApiKeyUsageCreate, db: Session = Depends(get_db)):
    """
    记录API密钥使用信息。
    """
    # 记录使用情况
    if not usage.status:
        logger.warning(f"API密钥使用失败: {usage.api_key[:8]}... 模型: {usage.model_name} 源: {usage.source_name}")
    else:
        logger.debug(f"记录API密钥使用情况: {usage.api_key[:8]}... 状态: {usage.status}")
    
    # 创建数据库记录
    db_usage = ApiKeyUsage(
        request_id=usage.request_id,
        api_key=usage.api_key,
        model_name=usage.model_name,
        source_name=usage.source_name,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        create_time=usage.create_time,
        finish_time=usage.finish_time,
        execution_time=usage.execution_time,
        status=usage.status,
        remark=usage.remark or ""
    )
    
    try:
        db.add(db_usage)
        db.commit()
        db.refresh(db_usage)
        logger.debug("API密钥使用情况已成功记录到数据库")
    except Exception as e:
        db.rollback()
        logger.error(f"记录API密钥使用情况到数据库时失败: {str(e)}")
        raise HTTPException(status_code=500, detail="记录到数据库失败")
    
    return {"message": "API密钥使用情况已成功记录"}

# ==================== 管理端点 ====================

@app.get("/stats", response_model=Dict)
async def get_stats():
    """获取API密钥统计信息"""
    return {
        "last_update": last_update_time.isoformat(),
        "failed_keys_by_source": {source: len(keys) for source, keys in failed_keys_cache.items()},
        "total_failed_keys": sum(len(keys) for keys in failed_keys_cache.values()),
        "detailed_stats": dict(stats_cache)
    }

@app.post("/refresh_cache")
async def refresh_cache():
    """手动刷新失败密钥缓存"""
    logger.info("收到手动刷新缓存请求")
    try:
        update_failed_keys_cache()
        return {"message": "缓存刷新成功", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"手动刷新缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刷新缓存失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info") 