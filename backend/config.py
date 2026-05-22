"""
配置管理模块
Author: ch

核心知识点:
  1. Pydantic Settings 自动读取 .env → 无需手动 os.getenv()
  2. Field(alias="ENV_VAR") 实现环境变量名 ↔ Python 属性名映射
  3. model_config(env_file=".env") 指定配置文件路径
  4. @property 装饰器将方法伪装为属性，调用时不用写括号

数据流:
  .env 文件  →  Settings 类  →  settings 全局单例  →  各模块 import 使用
"""

import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    应用配置类 — 单例模式，整个项目共享一个实例

    Pydantic Settings 加载优先级（从高到低）:
      1. 系统环境变量（export DASHSCOPE_API_KEY=xxx）
      2. .env 文件
      3. Field(default=...) 默认值
    """

    model_config = SettingsConfigDict(
        env_file=".env",              # ← Pydantic 自动读取 .env 的秘密
        env_file_encoding="utf-8",
        extra="ignore",               # 忽略 .env 中未定义的字段
    )

    # ──────────── 百炼（DashScope）LLM 配置 ────────────
    # API Key 从阿里云百炼控制台获取: https://bailian.console.aliyun.com
    dashscope_api_key: str = Field(
        default="",
        alias="DASHSCOPE_API_KEY",
        description="百炼 API 密钥，必填",
    )
    llm_model: str = Field(
        default="qwen-plus",
        alias="LLM_MODEL",
        description="LLM 模型名: qwen-plus(推荐) / qwen-max(最强) / qwen-turbo(最快)",
    )
    embedding_model: str = Field(
        default="text-embedding-v4",
        alias="EMBEDDING_MODEL",
        description="嵌入模型名: text-embedding-v4(推荐) / text-embedding-v3",
    )

    # ──────────── ChromaDB 向量数据库 ────────────
    chroma_persist_dir: str = Field(
        default="data/chroma_db",
        alias="CHROMA_PERSIST_DIR",
        description="向量数据持久化目录，重启不丢失",
    )

    # ──────────── 文件上传 ────────────
    upload_dir: str = Field(
        default="data/uploads",
        alias="UPLOAD_DIR",
        description="原始文件保存目录",
    )
    # ──────────── 微信小程序 ────────────
    wx_appid: str = Field(
        default="", alias="WX_APPID", description="小程序 AppID"
    )
    wx_secret: str = Field(
        default="", alias="WX_SECRET", description="小程序 AppSecret"
    )

    max_upload_size_mb: int = Field(
        default=20,
        alias="MAX_UPLOAD_SIZE_MB",
        description="上传文件大小上限(MB)",
    )

    # ──────────── MySQL 数据库 ────────────
    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="root", alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="multi_agent", alias="MYSQL_DATABASE")

    # ──────────── 服务 ────────────
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=True, alias="DEBUG")

    # ──────────── 派生属性 ────────────
    @property
    def mysql_url(self) -> str:
        """
        异步 MySQL 连接串 (aiomysql 驱动)

        格式: mysql+aiomysql://user:password@host:port/database
        为什么用 aiomysql?
          - FastAPI 是异步框架，同步驱动会阻塞整个事件循环
          - aiomysql 基于 asyncio，不阻塞其他请求
        """
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def mysql_url_sync(self) -> str:
        """
        同步 MySQL 连接串 (pymysql 驱动)

        用途: Alembic 数据库迁移工具 —— 迁移脚本是同步执行的
        """
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


# ═══════════════════════════════════════════════════════════
# 全局单例
#   为什么用单例？
#     - Settings 只需读一次 .env，重复创建会反复读磁盘
#     - 所有模块 import settings 拿到的是同一个实例
#   注意: 如果改了 .env，需要重启服务才会生效
# ═══════════════════════════════════════════════════════════
settings = Settings()
logger.info(
    "配置加载完成 | LLM=%s | Embedding=%s | MySQL=%s:%s/%s",
    settings.llm_model,
    settings.embedding_model,
    settings.mysql_host,
    settings.mysql_port,
    settings.mysql_database,
)
