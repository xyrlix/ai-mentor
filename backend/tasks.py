from worker import celery_app
import time
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.document_loader import DocumentLoaderFactory
from rag.text_splitter import TextSplitter
from rag.vector_store import get_vector_store
from utils.redis import redis_cache


@celery_app.task
def process_document(file_path: str, file_ext: str, kb_id: int,
                     user_id: int) -> dict:
    """异步处理文档
    
    Args:
        file_path: 文件路径
        file_ext: 文件扩展名（不含.）
        kb_id: 知识库ID
        user_id: 用户ID
    
    Returns:
        处理结果字典
    """
    try:
        # 重新导入os模块，确保在函数内部可见
        import os
        # 1. 更新任务状态
        task_id = process_document.request.id
        redis_cache.set(f"task_status:{task_id}", {
            "status": "processing",
            "progress": 20
        })

        # 2. 加载文档
        time.sleep(1)  # 模拟处理时间
        loader = DocumentLoaderFactory.get_loader(file_ext)
        documents = loader.load(file_path)

        # 3. 更新进度
        redis_cache.set(f"task_status:{task_id}", {
            "status": "processing",
            "progress": 40
        })

        # 4. 分割文本
        time.sleep(1)
        text_splitter = TextSplitter()
        split_docs = text_splitter.split_documents(documents)

        # 5. 更新进度
        redis_cache.set(f"task_status:{task_id}", {
            "status": "processing",
            "progress": 60
        })

        # 6. 向量化（此处简化，实际需调用embedding模型）
        time.sleep(1)
        # 直接生成随机向量，实际项目中应调用embedding模型
        import numpy as np
        texts = [doc['chunk_content'] for doc in split_docs]
        # 生成随机向量（简化实现）
        embeddings = [np.random.rand(1024) for _ in texts]

        # 7. 更新进度
        redis_cache.set(f"task_status:{task_id}", {
            "status": "processing",
            "progress": 80
        })

        # 8. 存入pgvector
        time.sleep(1)
        vector_store = get_vector_store()
        vector_store.add_chunks(kb_id, split_docs, embeddings)

        # 9. 更新进度
        redis_cache.set(f"task_status:{task_id}", {
            "status": "completed",
            "progress": 100
        })

        # 10. 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "success",
            "message": "文档处理完成",
            "document_count": len(documents),
            "chunk_count": len(split_docs),
            "kb_id": kb_id,
            "user_id": user_id
        }

    except Exception as e:
        # 11. 处理失败
        task_id = process_document.request.id
        redis_cache.set(f"task_status:{task_id}", {
            "status": "failed",
            "progress": 0,
            "error": str(e)
        })

        return {
            "status": "error",
            "message": f"文档处理失败: {str(e)}",
            "kb_id": kb_id,
            "user_id": user_id
        }


@celery_app.task
def update_document_status(kb_id: int, status: str) -> dict:
    """更新文档状态
    
    Args:
        kb_id: 知识库ID
        status: 状态（processing, completed, failed）
    
    Returns:
        更新结果字典
    """
    try:
        # 这里可以添加更新数据库中文档状态的逻辑
        return {
            "status": "success",
            "message": f"文档状态已更新为 {status}",
            "kb_id": kb_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"更新文档状态失败: {str(e)}",
            "kb_id": kb_id
        }
