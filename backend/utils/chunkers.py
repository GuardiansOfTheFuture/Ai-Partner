"""
文本分块器 — 三种策略 + 自动选择
Author: ch

═══════════════════════════════════════════════════════════════
三种分块策略对比:

策略          原理                          最佳场景          局限
────          ──                            ──               ──
Recursive     按分隔符优先级递归切分          通用、速度快      可能切断语义
Semantic      用嵌入模型检测语义断点          长文档、论文      慢、需调阈值
Markdown      按 # ## ### 标题层级切分        技术文档、Wiki    纯文本无效
═══════════════════════════════════════════════════════════════

选择建议:
  通用文本    → Recursive (默认, 够用)
  长文档/论文 → Semantic  (语义更完整)
  Markdown    → Markdown  (保留文档结构)
  混合文档库  → Auto      (自动检测类型)
"""

import logging
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 策略 1: Recursive — 按分隔符优先级递归切分
#   原理: 先用粗粒度分隔符（段落）切，切不动降级用更细的
#   优点: 快、稳定、不依赖外部 API
#   适合: 纯文本、对话记录、新闻稿
# ═══════════════════════════════════════════════════════════════

# 中文文档的天然边界优先级
CN_SEPARATORS = [
    "\n\n",   # 段落边界 → 最完整
    "\n",     # 换行
    "。",     # 句号 → 句子是最小语义单元
    "！",
    "？",
    "；",     # 分号
    "，",     # 逗号
    "、",     # 顿号
    " ",      # 英文词边界
    "",       # 逐字符 → 保底
]


def _create_recursive_splitter(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> RecursiveCharacterTextSplitter:
    """
    Recursive 策略 — 从粗到细逐级切分

    为什么分隔符按这个顺序？
      段落 > 句子 > 分句 > 词 > 字符
      算法优先在语义断点切，实在切不动才用更细的粒度。
      比如 "句号" 切出来的块比 "逗号" 切出来的语义更完整。
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CN_SEPARATORS,
        keep_separator=True,  # 保留分隔符 → 读起来更通顺
    )


# ═══════════════════════════════════════════════════════════════
# 策略 2: Semantic — 用嵌入模型找语义断点
#   原理: 将文本拆成句子 → 计算相邻句子的嵌入余弦距离
#         距离突然变大的位置 = 话题切换 = 最佳切分点
#   优点: 语义最完整，不会把相关句子切到两块
#   缺点: 慢（每次分块都要调嵌入 API）、阈值需要经验
#   适合: 论文、教材、长篇叙述文
# ═══════════════════════════════════════════════════════════════

def _create_semantic_splitter(
    chunk_size: int = 1000,
) -> "SemanticChunker":
    """
    Semantic 策略 — 基于语义相似度检测话题切换点

    原理图解:
      句子1: "Python 是动态类型语言..."     ─┐
      句子2: "变量不需要声明类型..."       ─┤ 嵌入向量很近 → 同一话题
      句子3: "Java 是静态类型语言..."       ─┘
      ─────────── 话题切换（断点）───────────
      句子4: "FastAPI 基于 Starlette..."   ─┐
      句子5: "支持异步和 WebSocket..."      ─┤ 嵌入向量很近 → 另一话题
      句子6: "性能接近 Node.js..."          ─┘

    阈值说明:
      percentile=90 → 相似度最低的 10% 位置作为断点
      值越小 = 断点越多 = 块越小
      推荐 85-95，中文文档建议 90
    """
    from langchain_experimental.text_splitter import SemanticChunker

    # 用百炼的嵌入模型做语义检测
    from backend.core.embeddings import get_embeddings
    embeddings = get_embeddings()

    return SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,  # 切在语义变化最大的 10% 处
        min_chunk_size=chunk_size // 4,  # 块太小的合并
    )


# ═══════════════════════════════════════════════════════════════
# 策略 3: Markdown-aware — 按标题层级切分
#   原理: # 一级标题 → 大块, ## 二级 → 中块, ### 三级 → 小块
#   优点: 保留文档结构，每块自带标题上下文
#   缺点: 纯文本无效，标题不规范时效果差
#   适合: 技术文档、API 文档、Wiki
# ═══════════════════════════════════════════════════════════════

MD_HEADERS = [
    ("#", "H1"),     # 一级标题
    ("##", "H2"),    # 二级标题
    ("###", "H3"),   # 三级标题
]


def _split_markdown(text: str) -> list[Document]:
    """
    Markdown 策略 — 按标题层级切分

    标题作为 metadata 的作用:
      检索时不仅匹配正文，还能匹配标题 → 准确性更高
      例如搜索 "安装步骤" → 即便正文没出现这个词，标题匹配也能命中
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=MD_HEADERS,
        strip_headers=False,  # 保留标题文字在 chunk 中
    )
    return splitter.split_text(text)


# ═══════════════════════════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════════════════════════

def chunk_document(
    text: str,
    metadata: dict | None = None,
    strategy: str = "auto",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Document]:
    """
    统一的文档分块入口

    Args:
        text:       原始文本
        metadata:   基础元数据 (document_id, file_name 等)
        strategy:   分块策略:
                      "recursive" → 按分隔符递归（默认推荐）
                      "semantic"  → 嵌入语义检测（慢但准）
                      "markdown"  → 按标题层级（有 # 时推荐）
                      "auto"      → 自动选择: 有标题用 markdown，否则 recursive
        chunk_size:  每块最大字符数（semantic 策略忽略此参数）
        chunk_overlap: 重叠字符数

    Returns:
        LangChain Document 列表，每个带 chunk_id, chunk_index

    策略自动选择逻辑 (auto):
      文本包含 # 开头的行  → markdown（保留文档结构）
      纯文本              → recursive（通用高效）
    """
    base_metadata = metadata or {}

    # ── 策略选择 ──
    if strategy == "auto":
        # 启发式检测: 前 500 字符包含 # 开头的行 → 很可能是 Markdown
        first_500 = text[:500]
        has_headers = any(
            line.strip().startswith("#") for line in first_500.split("\n")
        )
        strategy = "markdown" if has_headers else "recursive"
        logger.debug("自动选择策略 | 检测到标题=%s | 策略=%s", has_headers, strategy)

    logger.info("开始分块 | 策略=%s | chunk_size=%d | overlap=%d",
                strategy, chunk_size, chunk_overlap)

    # ── 执行分块 ──
    if strategy == "markdown":
        docs = _split_markdown(text)
        # 标题切分后的块可能还是太大，追加一次 recursive 细切
        if len(docs) <= 3:
            # 只有少数几个大块，说明标题层级不够 → 再用 recursive 细切
            recursive = _create_recursive_splitter(chunk_size, chunk_overlap)
            docs = recursive.create_documents(
                texts=[text], metadatas=[base_metadata],
            )

    elif strategy == "semantic":
        splitter = _create_semantic_splitter(chunk_size)
        docs = splitter.create_documents(
            texts=[text], metadatas=[base_metadata],
        )

    else:  # recursive (默认)
        splitter = _create_recursive_splitter(chunk_size, chunk_overlap)
        docs = splitter.create_documents(
            texts=[text], metadatas=[base_metadata],
        )

    # ── 追加唯一标识 ──
    for i, doc in enumerate(docs):
        doc.metadata.update(base_metadata)  # 合并基础元数据
        doc.metadata.setdefault("chunk_id", str(uuid.uuid4())[:8])
        doc.metadata["chunk_index"] = i

    logger.info("分块完成 | 块数=%d | 策略=%s", len(docs), strategy)
    return docs
