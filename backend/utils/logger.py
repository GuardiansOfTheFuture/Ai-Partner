"""
日志配置模块
Author: ch

使用方法:
  from backend.utils.logger import get_logger
  logger = get_logger(__name__)
  logger.info("这是一条日志")
  logger.error("出错了", exc_info=True)
"""

import logging
import sys

# 日志格式: 时间 | 级别 | 模块 | 消息
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """全局日志初始化 — 在 main.py 的 lifespan 中调用"""
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout,
    )
    # 抑制第三方库的冗余日志
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取模块级日志实例

    Args:
        name: 通常传 __name__，自动显示模块路径

    Returns:
        配置好的 Logger 实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("文档处理完成，共 %d 块", chunk_count)
    """
    return logging.getLogger(name)
