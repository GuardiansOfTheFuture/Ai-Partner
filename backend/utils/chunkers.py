"""
文本分块器
Author: ch
"""

import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter

CN_SEPARATORS = ["\n\n","\n","。","！","？","；","，","、"," ",""]


def chunk_document(text: str, metadata: dict | None = None, chunk_size=1000, chunk_overlap=200) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        separators=CN_SEPARATORS, keep_separator=True,
    )
    docs = splitter.create_documents(texts=[text], metadatas=[metadata or {}])
    for i, doc in enumerate(docs):
        doc.metadata["chunk_id"] = str(uuid.uuid4())[:8]
        doc.metadata["chunk_index"] = i
    return docs
