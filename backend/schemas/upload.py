from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class UploadResponse(BaseModel):
    """上传响应模型"""
    success: bool
    task_id: str
    message: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    kb_id: Optional[int] = None


class BatchUploadResponse(BaseModel):
    """批量上传响应模型"""
    success: bool
    task_id: str
    message: str
    file_count: int
    kb_id: Optional[int] = None


class TaskStatus(BaseModel):
    """任务状态模型"""
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    processed_files: Optional[int] = None
    total_files: Optional[int] = None
    current_file: Optional[str] = None
    current_result: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求模型"""
    user_id: int
    name: str
    domain: str  # it, language, cert
    sub_domain: Optional[str] = None  # backend, ielts, soft_high, etc.


class KnowledgeBaseResponse(BaseModel):
    """知识库响应模型"""
    id: int
    user_id: int
    name: str
    domain: str
    sub_domain: Optional[str] = None
    created_at: str
    document_count: Optional[int] = 0
    chunk_count: Optional[int] = 0