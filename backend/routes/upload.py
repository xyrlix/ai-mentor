import os
import shutil
import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from config import settings
from services.document_processor import get_document_processor
from rag.vector_store import get_vector_store, User
from schemas.upload import UploadResponse, BatchUploadResponse
from utils.redis import redis_cache

router = APIRouter(prefix="/api", tags=["文件上传"])

# 获取全局向量存储实例
vector_store = get_vector_store()

async def create_default_user(user_id: str) -> int:
    """创建默认用户"""
    try:
        # 使用vector_store中的User模型，它只有email字段
        from datetime import datetime
        
        # 创建一个数据库会话
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=vector_store.engine)
        db = SessionLocal()
        
        try:
            # 检查用户是否已存在（使用email作为用户标识）
            email = f"{user_id}@example.com"
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return existing_user.id
            
            # 创建新用户
            new_user = User(
                email=email,
                created_at=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"创建新用户: ID={new_user.id}, email={email}")
            return new_user.id
            
        finally:
            db.close()
        
    except Exception as e:
        print(f"创建用户失败: {e}")
        # 如果创建用户失败，返回一个默认的ID（比如1）
        return 1

async def create_knowledge_base(user_id: int,
                                name: str,
                                domain: str,
                                sub_domain: str = None) -> int:
    """创建知识库"""
    return vector_store.create_knowledge_base(user_id, name, domain, sub_domain)

# 支持的文档类型
SUPPORTED_EXTENSIONS = {
    '.pdf': 'pdf',
    '.docx': 'docx', 
    '.txt': 'txt'
}

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile) -> str:
    """验证文件类型和大小"""
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )
    
    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置文件指针
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {file_size} > {settings.MAX_FILE_SIZE}"
        )
    
    return SUPPORTED_EXTENSIONS[file_ext]


def save_upload_file(file: UploadFile) -> str:
    """保存上传的文件"""
    # 生成唯一的文件名
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def save_upload_file_with_content(file: UploadFile, content: bytes) -> str:
    """使用已读取的内容保存上传的文件"""
    # 生成唯一的文件名
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    return file_path


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),  # 改为接收字符串类型的user_id
    kb_id: Optional[int] = Form(None)  # 可选的知识库ID，如果不提供则创建新知识库
):
    """上传单个文档"""
    try:
        # 1. 检查文件大小
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制，最大允许 {settings.MAX_FILE_SIZE / (1024 * 1024)} MB"
            )

        # 2. 检查文件类型
        filename = file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型，仅允许: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 3. 保存上传的文件
        file_path = save_upload_file_with_content(file, content)
        file_type = file_ext[1:]  # 去掉.前缀

        # 4. 如果没有提供kb_id，创建新的知识库
        if kb_id is None:
            kb_name = os.path.splitext(filename)[0]
            user_id_int = int(user_id) if user_id.isdigit() else await create_default_user(user_id)
            kb_id = await create_knowledge_base(user_id_int, kb_name, "it", "backend")
        else:
            # 验证提供的kb_id是否存在
            vector_store = get_vector_store()
            kb = vector_store.get_knowledge_base_by_id(kb_id)
            if not kb:
                raise HTTPException(status_code=404, detail="知识库不存在")
            user_id_int = int(user_id) if user_id.isdigit() else await create_default_user(user_id)
        
        # 5. 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 6. 异步处理文档
        background_tasks.add_task(
            process_document_task, 
            task_id, file_path, kb_id, file_type
        )
        
        return UploadResponse(
            success=True,
            task_id=task_id,
            message="文档上传成功，正在处理中",
            file_path=file_path,
            file_type=file_type,
            kb_id=kb_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    kb_id: int = Form(...),
    user_id: int = Form(1)
):
    """批量上传文档"""
    try:
        # 验证所有文件
        file_paths = []
        file_types = []
        
        for file in files:
            file_type = validate_file(file)
            file_path = save_upload_file(file)
            file_paths.append(file_path)
            file_types.append(file_type)
        
        # 获取知识库信息
        vector_store = get_vector_store()
        kb = vector_store.get_knowledge_base_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 异步批量处理文档
        background_tasks.add_task(
            process_documents_batch_task,
            task_id, file_paths, kb_id, file_types
        )
        
        return BatchUploadResponse(
            success=True,
            task_id=task_id,
            message=f"批量上传成功，共 {len(files)} 个文件，正在处理中",
            file_count=len(files),
            kb_id=kb_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task_status = redis_cache.get(f"task:{task_id}")
    if not task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return JSONResponse(content=task_status)


# 后台任务函数
async def process_document_task(task_id: str, file_path: str, kb_id: int, file_type: str):
    """处理单个文档的后台任务"""
    try:
        # 更新任务状态为进行中
        redis_cache.set(f"task:{task_id}", {
            "status": "processing",
            "progress": 0,
            "message": "开始处理文档"
        })
        
        # 处理文档
        document_processor = get_document_processor()
        result = document_processor.process_document(file_path, kb_id, file_type)
        
        # 更新任务状态
        if result["success"]:
            redis_cache.set(f"task:{task_id}", {
                "status": "completed",
                "progress": 100,
                "message": result["message"],
                "result": result
            })
        else:
            redis_cache.set(f"task:{task_id}", {
                "status": "failed",
                "progress": 0,
                "message": result["message"],
                "error": result.get("error", "")
            })
            
    except Exception as e:
        redis_cache.set(f"task:{task_id}", {
            "status": "failed",
            "progress": 0,
            "message": f"处理失败: {str(e)}",
            "error": str(e)
        })


async def process_documents_batch_task(task_id: str, file_paths: List[str], kb_id: int, file_types: List[str]):
    """批量处理文档的后台任务"""
    try:
        total_files = len(file_paths)
        
        # 更新任务状态
        redis_cache.set(f"task:{task_id}", {
            "status": "processing",
            "progress": 0,
            "message": f"开始批量处理 {total_files} 个文档",
            "processed_files": 0,
            "total_files": total_files
        })
        
        # 批量处理文档
        document_processor = get_document_processor()
        
        for i, (file_path, file_type) in enumerate(zip(file_paths, file_types)):
            # 处理单个文档
            result = document_processor.process_document(file_path, kb_id, file_type)
            
            # 更新进度
            progress = int((i + 1) / total_files * 100)
            redis_cache.set(f"task:{task_id}", {
                "status": "processing",
                "progress": progress,
                "message": f"正在处理第 {i + 1} 个文档",
                "processed_files": i + 1,
                "total_files": total_files,
                "current_file": os.path.basename(file_path),
                "current_result": result
            })
        
        # 最终结果
        final_result = document_processor.batch_process_documents(file_paths, kb_id, file_types)
        
        redis_cache.set(f"task:{task_id}", {
            "status": "completed",
            "progress": 100,
            "message": final_result["message"],
            "result": final_result
        })
        
    except Exception as e:
        redis_cache.set(f"task:{task_id}", {
            "status": "failed",
            "progress": 0,
            "message": f"批量处理失败: {str(e)}",
            "error": str(e)
        })