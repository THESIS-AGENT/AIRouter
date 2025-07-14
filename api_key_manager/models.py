from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, create_engine, ForeignKey, inspect, text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import time
import logging
from datetime import datetime

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取数据库连接详情
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", None)
DB_NAME = os.environ.get("DB_NAME", "airouter")
DB_PORT = os.environ.get("DB_PORT", "3306")

# 检查必需的环境变量
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD 环境变量必须设置！请设置数据库密码环境变量。")

# 创建数据库URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建基类
Base = declarative_base()

# 定义API密钥使用模型
class ApiKeyUsage(Base):
    """记录API密钥使用情况和性能的模型."""
    __tablename__ = "api_key_usage"

    request_id = Column(String(100), primary_key=True, index=True)
    api_key = Column(String(200), index=True, nullable=False)
    model_name = Column(String(100), index=True, nullable=False)
    source_name = Column(String(100), index=True, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    create_time = Column(DateTime, nullable=False)
    finish_time = Column(DateTime, nullable=False, index=True)  # 添加索引
    execution_time = Column(Float, nullable=False)
    status = Column(Boolean, nullable=False, default=True, index=True)  # 添加索引
    remark = Column(String(255), nullable=True, default="")

    # 定义复合索引 - 针对失败密钥查询优化
    __table_args__ = (
        # 主要查询索引：按API密钥、状态、完成时间查询失败记录
        Index('idx_api_key_status_finish_time', 'api_key', 'status', 'finish_time'),
        # 按源名称和状态查询统计
        Index('idx_source_status_finish_time', 'source_name', 'status', 'finish_time'),
        # 按模型名称和状态查询统计
        Index('idx_model_status_finish_time', 'model_name', 'status', 'finish_time'),
        # 按源名称和模型名称查询统计
        Index('idx_source_model_finish_time', 'source_name', 'model_name', 'finish_time'),
        # 时间范围查询索引
        Index('idx_finish_time_status', 'finish_time', 'status'),
    )

    def __repr__(self):
        return f"<ApiKeyUsage(request_id='{self.request_id}', api_key='{self.api_key[:5]}...', status={self.status}, remark='{self.remark}')>"

# 创建带有重试机制的数据库引擎
def get_engine(retries=5, delay=2):
    """尝试创建数据库引擎并处理连接错误"""
    for attempt in range(retries):
        try:
            logger.info(f"尝试连接到数据库: {DB_HOST}:{DB_PORT}, 尝试 {attempt+1}/{retries}")
            # 添加connect_args以提高连接可靠性
            engine = create_engine(
                DATABASE_URL, 
                pool_pre_ping=True,  # 检查连接是否活跃
                pool_recycle=3600,   # 一小时后回收连接
                pool_size=20,        # 增加连接池大小，默认为5
                max_overflow=30,     # 增加溢出连接数，默认为10
                pool_timeout=60,     # 增加等待可用连接的超时时间（秒）
                connect_args={
                    "connect_timeout": 30  # 连接超时时间（秒）
                }
            )
            # 测试连接
            connection = engine.connect()
            connection.close()
            logger.info("数据库连接成功")
            return engine
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            if attempt < retries - 1:
                logger.info(f"将在 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                logger.error("所有数据库连接尝试均失败")
                raise Exception("无法连接到数据库，已达到最大重试次数")

# 初始化数据库
try:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"创建数据库引擎时出错: {str(e)}")
    raise

# 创建数据库表
def create_tables():
    """创建所有数据库表，如果表已存在则跳过，并处理表结构迁移"""
    try:
        # 创建检查器实例
        inspector = inspect(engine)
        
        # 检查是否已存在 api_key_usage 表
        if inspector.has_table(ApiKeyUsage.__tablename__):
            logger.info(f"表 '{ApiKeyUsage.__tablename__}' 已存在，检查字段和索引更新...")
            
            # 检查 remark 字段是否存在
            columns = inspector.get_columns(ApiKeyUsage.__tablename__)
            column_names = [col['name'] for col in columns]
            
            if 'remark' not in column_names:
                logger.info("添加 remark 字段到现有表...")
                # 执行 ALTER TABLE 语句添加 remark 字段
                with engine.begin() as connection:
                    connection.execute(
                        text(f"ALTER TABLE {ApiKeyUsage.__tablename__} ADD COLUMN remark VARCHAR(255) DEFAULT '' COMMENT '备注信息，用于记录API调用的用途或来源'")
                    )
                logger.info("remark 字段添加成功")
            else:
                logger.info("remark 字段已存在，跳过添加")
            
            # 检查并添加索引
            existing_indexes = inspector.get_indexes(ApiKeyUsage.__tablename__)
            existing_index_names = {idx['name'] for idx in existing_indexes}
            
            # 需要添加的索引
            indexes_to_add = [
                ("idx_api_key_status_finish_time", ["api_key", "status", "finish_time"]),
                ("idx_source_status_finish_time", ["source_name", "status", "finish_time"]),
                ("idx_model_status_finish_time", ["model_name", "status", "finish_time"]),
                ("idx_source_model_finish_time", ["source_name", "model_name", "finish_time"]),
                ("idx_finish_time_status", ["finish_time", "status"]),
            ]
            
            with engine.begin() as connection:
                for index_name, columns in indexes_to_add:
                    if index_name not in existing_index_names:
                        logger.info(f"添加索引: {index_name}")
                        columns_str = ", ".join(columns)
                        connection.execute(
                            text(f"CREATE INDEX {index_name} ON {ApiKeyUsage.__tablename__} ({columns_str})")
                        )
                    else:
                        logger.info(f"索引 {index_name} 已存在，跳过添加")
                        
            logger.info("索引检查和添加完成")
        else:
            # 只有当表不存在时才创建
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表或更新表结构时出错: {str(e)}")
        raise

# 获取数据库会话
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 