from abc import ABC, abstractmethod
from typing import List, Dict
import PyPDF2
from docx import Document


class DocumentLoader(ABC):
    """文档加载器抽象基类"""
    
    @abstractmethod
    def load(self, file_path: str) -> List[Dict]:
        """加载文档"""
        pass


class PDFLoader(DocumentLoader):
    """PDF文档加载器"""
    
    def load(self, file_path: str) -> List[Dict]:
        """加载PDF文档并返回内容列表"""
        documents = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    documents.append({
                        'page': page_num + 1,
                        'content': text,
                        'file_path': file_path
                    })
        return documents


class WordLoader(DocumentLoader):
    """Word文档加载器"""
    
    def load(self, file_path: str) -> List[Dict]:
        """加载Word文档并返回内容列表"""
        documents = []
        doc = Document(file_path)
        for para_num, para in enumerate(doc.paragraphs):
            if para.text.strip():
                documents.append({
                    'paragraph': para_num + 1,
                    'content': para.text,
                    'file_path': file_path
                })
        return documents


class TextLoader(DocumentLoader):
    """文本文件加载器"""
    
    def load(self, file_path: str) -> List[Dict]:
        """加载文本文件并返回内容列表"""
        documents = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            documents.append({
                'content': content,
                'file_path': file_path
            })
        return documents


class DocumentLoaderFactory:
    """文档加载器工厂类"""
    
    @staticmethod
    def get_loader(file_type: str) -> DocumentLoader:
        """根据文件类型获取对应的加载器"""
        loaders = {
            'pdf': PDFLoader(),
            'docx': WordLoader(),
            'txt': TextLoader()
        }
        return loaders.get(file_type.lower(), TextLoader())
