from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import text
import numpy as np
import datetime

# 只有在PostgreSQL数据库时才使用pgvector
use_pgvector = False
from config import settings
if "postgresql" in settings.DATABASE_URL:
    from pgvector.sqlalchemy import Vector
    use_pgvector = True

# 修复导入路径
import sys
import os
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

from utils.redis import redis_cache

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # 关联到知识库
    knowledge_bases = relationship("KnowledgeBase", back_populates="user")


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    domain = Column(String(20), nullable=False)  # 'it', 'language', 'cert'
    sub_domain = Column(String(50))  # 'backend', 'ielts', 'soft_high'
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # 关联到用户和文档
    user = relationship("User", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base")
    chunks = relationship("Chunk", back_populates="knowledge_base")


class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # 关联到知识库和文档块
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document")


class Chunk(Base):
    """文档块表，存储向量化的文本片段"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON)  # 避免使用SQLAlchemy保留字'metadata'
    
    # 根据数据库类型选择embedding字段类型
    if use_pgvector:
        embedding = Column(Vector(1024), nullable=False)  # PostgreSQL + pgvector
    else:
        embedding = Column(JSON, nullable=False)  # SQLite使用JSON存储向量
        
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # 关联到知识库和文档
    knowledge_base = relationship("KnowledgeBase", back_populates="chunks")
    document = relationship("Document", back_populates="chunks")


class VectorStore:
    """向量存储操作类"""
    
    def __init__(self, db_url: str = None):
        """初始化向量存储
        
        Args:
            db_url: 数据库连接URL
        """
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_knowledge_base(self, user_id: int, name: str, domain: str, sub_domain: str = None) -> int:
        """创建知识库"""
        db = self.SessionLocal()
        try:
            kb = KnowledgeBase(
                user_id=user_id,
                name=name,
                domain=domain,
                sub_domain=sub_domain,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(kb)
            db.commit()
            db.refresh(kb)
            return kb.id
        finally:
            db.close()
    
    def add_document(self, kb_id: int, file_path: str, file_type: str, content: str) -> int:
        """添加文档到知识库"""
        db = self.SessionLocal()
        try:
            doc = Document(
                kb_id=kb_id,
                file_path=file_path,
                file_type=file_type,
                content=content,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return doc.id
        finally:
            db.close()
    
    def add_chunks(self, kb_id: int, chunks: List[Dict[str, Any]], embeddings: List[np.ndarray], document_id: int = None):
        """添加文档块和向量
        
        Args:
            kb_id: 知识库ID
            chunks: 文档块列表
            embeddings: 向量列表
            document_id: 文档ID（可选）
        """
        db = self.SessionLocal()
        try:
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                # 确保emb是NumPy数组
                if not isinstance(emb, np.ndarray):
                    emb = np.array(emb)
                    
                chunk_obj = Chunk(
                    kb_id=kb_id,
                    document_id=document_id,
                    content=chunk.get("chunk_content", ""),
                    chunk_metadata=chunk.get("metadata", {}),
                    embedding=emb.tolist(),
                    created_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(chunk_obj)
            db.commit()
        finally:
            db.close()
    
    def similarity_search(self, query_vector: List[float], kb_id: int, top_k: int = 5) -> List[Dict]:
        """向量相似度搜索，带Redis缓存
        
        Args:
            query_vector: 查询向量
            kb_id: 知识库ID
            top_k: 返回结果数量
        
        Returns:
            相似文档块列表
        """
        # 1. 生成缓存键
        query_str = f"{kb_id}_{top_k}_{str(query_vector[:10])}"  # 使用向量前10个值作为缓存键的一部分
        cache_key = f"similarity_search:{hashlib.md5(query_str.encode()).hexdigest()}"
        
        # 2. 尝试从缓存获取
        cached_result = redis_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 3. 执行向量搜索
        db = self.SessionLocal()
        try:
            # 获取所有相关文档块
            chunks = db.query(Chunk).filter(Chunk.kb_id == kb_id).all()
            
            # 计算余弦相似度
            def cosine_similarity(vec1, vec2):
                """计算两个向量的余弦相似度"""
                if not vec1 or not vec2:
                    return 0
                dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
                norm1 = sum(v ** 2 for v in vec1) ** 0.5
                norm2 = sum(v ** 2 for v in vec2) ** 0.5
                if norm1 == 0 or norm2 == 0:
                    return 0
                return dot_product / (norm1 * norm2)
            
            # 对所有文档块计算相似度
            results = []
            for chunk in chunks:
                # 处理不同数据库的embedding存储格式
                if use_pgvector:
                    # PostgreSQL + pgvector: embedding是Vector类型
                    chunk_embedding = chunk.embedding.tolist()
                else:
                    # SQLite: embedding是JSON类型
                    chunk_embedding = chunk.embedding
                
                similarity = cosine_similarity(query_vector, chunk_embedding)
                results.append({
                    'id': chunk.id,
                    'kb_id': chunk.kb_id,
                    'document_id': chunk.document_id,
                    'content': chunk.content,
                    'metadata': chunk.chunk_metadata,
                    'embedding': chunk_embedding,
                    'similarity': similarity
                })
            
            # 按相似度排序，取top_k个结果
            results.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = results[:top_k]
            
            # 移除临时的similarity字段
            for result in top_results:
                result.pop('similarity', None)
            
            # 4. 将结果存入缓存，过期时间30分钟
            redis_cache.set(cache_key, top_results, expire=settings.CACHE_EXPIRE_MINUTES * 60)
            
            return top_results
        finally:
            db.close()
    
    def hybrid_search(self, query_vector: List[float], keyword: str, kb_id: int, top_k: int = 5) -> List[Dict]:
        """混合搜索：向量搜索 + 关键词搜索"""
        db = self.SessionLocal()
        try:
            # 1. 获取所有相关文档块
            all_chunks = db.query(Chunk).filter(Chunk.kb_id == kb_id).all()
            
            # 2. 计算余弦相似度
            def cosine_similarity(vec1, vec2):
                """计算两个向量的余弦相似度"""
                if not vec1 or not vec2:
                    return 0
                dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
                norm1 = sum(v ** 2 for v in vec1) ** 0.5
                norm2 = sum(v ** 2 for v in vec2) ** 0.5
                if norm1 == 0 or norm2 == 0:
                    return 0
                return dot_product / (norm1 * norm2)
            
            # 3. 对所有文档块计算相似度和关键词匹配
            results = []
            for chunk in all_chunks:
                # 处理不同数据库的embedding存储格式
                if use_pgvector:
                    chunk_embedding = chunk.embedding.tolist()
                else:
                    chunk_embedding = chunk.embedding
                
                # 计算向量相似度
                vector_similarity = cosine_similarity(query_vector, chunk_embedding)
                
                # 计算关键词匹配得分
                keyword_score = 1.0 if keyword.lower() in chunk.content.lower() else 0.0
                
                # 综合得分（可以调整权重）
                total_score = vector_similarity * 0.7 + keyword_score * 0.3
                
                results.append({
                    'id': chunk.id,
                    'kb_id': chunk.kb_id,
                    'document_id': chunk.document_id,
                    'content': chunk.content,
                    'metadata': chunk.chunk_metadata,
                    'embedding': chunk_embedding,
                    'score': total_score
                })
            
            # 4. 按综合得分排序，取top_k个结果
            results.sort(key=lambda x: x['score'], reverse=True)
            top_results = results[:top_k]
            
            # 移除临时的score字段
            for result in top_results:
                result.pop('score', None)
            
            return top_results
        finally:
            db.close()
    
    def get_knowledge_base_by_id(self, kb_id: int) -> Optional[KnowledgeBase]:
        """根据ID获取知识库"""
        db = self.SessionLocal()
        try:
            return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        finally:
            db.close()
    
    def get_chunks_by_kb_id(self, kb_id: int, limit: int = 100) -> List[Chunk]:
        """根据知识库ID获取文档块"""
        db = self.SessionLocal()
        try:
            return db.query(Chunk).filter(Chunk.kb_id == kb_id).limit(limit).all()
        finally:
            db.close()


# 工具函数
import time

def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    return VectorStore(settings.DATABASE_URL)
