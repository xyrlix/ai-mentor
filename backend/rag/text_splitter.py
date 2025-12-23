from typing import List, Dict
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter


class TextSplitter:
    """文本分割器，用于将长文本切分为语义连贯的小块"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """初始化文本分割器
        
        Args:
            chunk_size: 每个文本块的大小
            chunk_overlap: 文本块之间的重叠大小
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", "", ".", ";", ",", " "])

    def split_text(self, text: str) -> List[str]:
        """分割单段文本"""
        return self.splitter.split_text(text)

    def split_documents(self, documents: List[Dict]) -> List[Dict]:
        """分割文档列表"""
        split_docs = []
        for doc in documents:
            chunks = self.split_text(doc['content'])
            for i, chunk in enumerate(chunks):
                split_docs.append({
                    **doc, 'chunk_id': i + 1,
                    'chunk_content': chunk,
                    'original_content': doc['content']
                })
        return split_docs

    def split_long_text(self, text: str, max_length: int = 500) -> List[str]:
        """分割超长文本，确保每个片段不超过指定长度"""
        # 先按段落分割
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前段落本身就超过最大长度，递归分割
            if len(para) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # 递归分割长段落
                sub_chunks = self.split_long_text(para, max_length)
                chunks.extend(sub_chunks)
            else:
                # 如果添加当前段落会超过长度，先保存当前块
                if len(current_chunk) + len(para) + 2 > max_length:
                    chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
