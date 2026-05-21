"""
LLM 工厂模块
Author: ch

核心知识点:
  1. ChatTongyi = 百炼官方 LangChain 适配器，封装了 API 调用细节
  2. temperature 控制生成随机性:
       0.0 = 确定性输出（RAG 首选，同样的问题总是得到同样答案）
       0.7 = 高创意（适合写文章、头脑风暴）
       1.0+ = 胡说八道概率显著上升
  3. 工厂模式: 不直接 new 对象，通过函数获取 → 方便切换模型/参数
  4. streaming=False(同步) vs streaming=True(流式) → Phase 4 讲 WebSocket 时展开

模型选择:
  qwen-plus   → 性价比之选，9成场景够用
  qwen-max    → 复杂推理、长文理解
  qwen-turbo  → 速度优先，简单问答
"""

import logging

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.language_models import BaseChatModel

from backend.config import settings

logger = logging.getLogger(__name__)


def get_llm(
    model: str | None = None,
    temperature: float = 0.5,
    streaming: bool = False,
) -> BaseChatModel:
    """
    获取百炼 LLM 实例（工厂函数）

    为什么用工厂函数而不是全局变量？
      1. 不同场景需要不同 temperature
      2. 不同场景可能需要不同模型（省钱用 qwen-turbo，复杂任务用 qwen-max）
      3. Phase 4 流式输出需要 streaming=True

    Args:
        model: 模型名称，None=用配置文件默认值
        temperature: 0.0(精确) ~ 1.0(创意)，RAG 场景强烈建议 0.0
        streaming: 是否启用流式输出，默认 False

    Returns:
        BaseChatModel 实例 —— LangChain 标准接口，所有 LLM 都遵循
    """
    model = model or settings.llm_model

    if not settings.dashscope_api_key:
        raise ValueError(
            "DASHSCOPE_API_KEY 未设置！\n"
            "请在 .env 文件中配置: DASHSCOPE_API_KEY=sk-你的密钥\n"
            "获取地址: https://bailian.console.aliyun.com"
        )

    logger.debug("创建 LLM 实例 | model=%s | temperature=%.1f | streaming=%s",
                 model, temperature, streaming)

    return ChatTongyi(
        model=model,
        temperature=temperature,
        streaming=streaming,
        dashscope_api_key=settings.dashscope_api_key,
    )


def get_llm_creative() -> BaseChatModel:
    """
    高创意度 LLM — temperature=0.7

    适用场景: 摘要生成、头脑风暴、文案撰写
    不适用: 事实问答、代码生成（会"发挥想象力"）
    """
    logger.debug("获取创意型 LLM")
    return get_llm(temperature=0.7)


def get_llm_precise() -> BaseChatModel:
    """
    高精度 LLM — temperature=0.0

    适用场景: 事实问答、信息提取、代码生成
    temperature=0 时 LLM 每次输出几乎一致，适合需要稳定结果的场景
    """
    logger.debug("获取精确型 LLM")
    return get_llm(temperature=0.0)
