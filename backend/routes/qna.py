from fastapi import APIRouter, HTTPException, Query, Form
from typing import List, Dict, Any, Optional
import asyncio

# 导入相关模块
from rag.vector_store import get_vector_store
from agent.qna_agent import get_qna_agent
from utils.redis import redis_cache

router = APIRouter(prefix="/api/qna", tags=["智能问答"])

# 获取组件实例
vector_store = get_vector_store()
qna_agent = get_qna_agent()


@router.post("/ask")
async def ask_question(
    question: str = Form(..., description="用户问题"),
    kb_id: int = Form(..., description="知识库ID"),
    user_id: str = Form(..., description="用户ID"),
    conversation_mode: bool = Form(False, description="是否启用多轮对话模式")
) -> Dict[str, Any]:
    """智能问答接口"""
    try:
        # 1. RAG检索：获取相关上下文
        # 简化实现：生成随机向量进行检索
        import numpy as np
        query_vector = np.random.rand(1024).tolist()
        
        context_docs = vector_store.similarity_search(query_vector, kb_id, top_k=3)
        context = "\n".join([d["content"] for d in context_docs])
        
        # 2. 获取对话历史（简化实现）
        history_key = f"conversation_history:{user_id}:{kb_id}"
        history = redis_cache.get(history_key) or ""
        
        # 3. 调用问答Agent
        result = qna_agent.answer_question(
            question=question,
            context=context,
            history=history,
            conversation_mode=conversation_mode
        )
        
        # 4. 更新对话历史
        if conversation_mode:
            new_history = f"{history}\n用户: {question}\n助手: {result.get('answer', '')}"
            # 限制历史长度（保留最近10轮对话）
            history_lines = new_history.strip().split('\n')
            if len(history_lines) > 20:  # 10轮对话
                history_lines = history_lines[-20:]
            new_history = '\n'.join(history_lines)
            redis_cache.set(history_key, new_history, expire=3600)  # 1小时过期
        
        # 5. 返回结果
        return {
            "status": "success",
            "question": question,
            "answer": result.get("answer", ""),
            "confidence": result.get("confidence", 0.8),
            "sources": result.get("sources", []),
            "context_docs": context_docs,
            "conversation_mode": conversation_mode,
            "history_updated": conversation_mode
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@router.post("/evaluate")
async def evaluate_answer(
    question: str = Form(..., description="问题"),
    answer: str = Form(..., description="回答"),
    expected_answer: Optional[str] = Form(None, description="期望答案（可选）")
) -> Dict[str, Any]:
    """评估回答质量"""
    try:
        result = qna_agent.evaluate_answer_quality(
            question=question,
            answer=answer,
            expected_answer=expected_answer
        )
        
        return {
            "status": "success",
            "evaluation": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@router.post("/related-questions")
async def get_related_questions(
    question: str = Form(..., description="原始问题"),
    kb_id: int = Form(..., description="知识库ID")
) -> Dict[str, Any]:
    """获取相关问题"""
    try:
        # 获取相关上下文
        import numpy as np
        query_vector = np.random.rand(1024).tolist()
        context_docs = vector_store.similarity_search(query_vector, kb_id, top_k=2)
        context = "\n".join([d["content"] for d in context_docs])
        
        # 生成相关问题
        related_questions = qna_agent.generate_related_questions(
            question=question,
            context=context
        )
        
        return {
            "status": "success",
            "original_question": question,
            "related_questions": related_questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成相关问题失败: {str(e)}")


@router.get("/conversation-history/{user_id}/{kb_id}")
async def get_conversation_history(
    user_id: str,
    kb_id: int
) -> Dict[str, Any]:
    """获取对话历史"""
    try:
        history_key = f"conversation_history:{user_id}:{kb_id}"
        history = redis_cache.get(history_key) or ""
        
        return {
            "status": "success",
            "user_id": user_id,
            "kb_id": kb_id,
            "history": history,
            "history_count": len(history.split("\n")) // 2 if history else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")


@router.delete("/conversation-history/{user_id}/{kb_id}")
async def clear_conversation_history(
    user_id: str,
    kb_id: int
) -> Dict[str, Any]:
    """清空对话历史"""
    try:
        history_key = f"conversation_history:{user_id}:{kb_id}"
        redis_cache.delete(history_key)
        
        return {
            "status": "success",
            "message": "对话历史已清空"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空对话历史失败: {str(e)}")


@router.get("/knowledge-base-info/{kb_id}")
async def get_knowledge_base_info(kb_id: int) -> Dict[str, Any]:
    """获取知识库信息"""
    try:
        kb = vector_store.get_knowledge_base_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档块数量
        chunks = vector_store.get_chunks_by_kb_id(kb_id, limit=1000)
        
        return {
            "status": "success",
            "knowledge_base": {
                "id": kb.id,
                "name": kb.name,
                "domain": kb.domain,
                "sub_domain": kb.sub_domain,
                "created_at": kb.created_at.isoformat() if kb.created_at else None
            },
            "chunk_count": len(chunks),
            "document_count": len(set([chunk.document_id for chunk in chunks if chunk.document_id]))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库信息失败: {str(e)}")