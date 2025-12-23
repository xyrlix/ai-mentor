from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
import time
import json
from typing import List, Dict, Any, Optional
import asyncio

# 添加当前目录到Python路径
import sys

sys.path.append('.')

from config import settings, LLM_CONFIG
from rag.document_loader import DocumentLoaderFactory
from rag.text_splitter import TextSplitter
from rag.vector_store import VectorStore, get_vector_store
from agent.interviewer import InterviewerAgent
from report.generator import ReportGenerator

# 数据库和认证相关
from database import init_db, get_db
from sqlalchemy.orm import Session
from models import User
from routes.auth import router as auth_router

# 配置速率限制相关
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.config import Config

# 创建FastAPI应用
app = FastAPI(title="AI Mentor API",
              description="AI面试助手API服务",
              version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置速率限制
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT}/minute"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 包含认证路由
app.include_router(auth_router)

# 包含支付路由
from routes import payment

app.include_router(payment.router)

# 包含语音服务路由
from routes import speech

app.include_router(speech.router)

# 包含问答路由
from routes import qna

app.include_router(qna.router)

# 包含考试路由
from routes import exam

app.include_router(exam.router)

# 包含上传路由
from routes import upload

app.include_router(upload.router)


# 数据库初始化
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    await init_db()
    print("数据库初始化完成")

    # 确保uploads目录存在
    os.makedirs("uploads", exist_ok=True)
    print("启动完成")


# 初始化组件
vector_store = get_vector_store()
text_splitter = TextSplitter()
report_generator = ReportGenerator()

# 延迟初始化InterviewerAgent，避免在启动时就需要API密钥
interviewer_agent = None


def get_interviewer_agent():
    global interviewer_agent
    if interviewer_agent is None:
        interviewer_agent = InterviewerAgent()
    return interviewer_agent


# 基本路由
@app.get("/")
def root():
    return {"message": "AI Mentor API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 辅助函数
async def load_and_split_document(file_path: str, file_type: str):
    """加载并切分文档"""
    loader = DocumentLoaderFactory.get_loader(file_type)
    documents = loader.load(file_path)
    return text_splitter.split_documents(documents)


async def embed(texts: List[str]) -> List[List[float]]:
    """生成文本的向量嵌入（简化实现，实际需调用embedding模型）"""
    # 这里应该调用实际的embedding模型，如BGE-large-zh-v1.5
    # 简化实现：生成随机向量
    import numpy as np
    return [np.random.rand(settings.VECTOR_DIMENSION).tolist() for _ in texts]


async def create_default_user(user_id: str) -> int:
    """创建默认用户"""
    try:
        # 使用数据库连接创建用户
        from database import get_db
        from models import User
        from sqlalchemy.orm import Session
        
        # 异步获取数据库会话
        async for db in get_db():
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == user_id).first()
            if existing_user:
                return existing_user.id
            
            # 创建新用户
            new_user = User(
                username=user_id,
                email=f"{user_id}@example.com",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"创建新用户: ID={new_user.id}, username={user_id}")
            return new_user.id
        
    except Exception as e:
        print(f"创建用户失败: {e}")
        # 如果创建用户失败，返回一个默认的ID（比如1）
        return 1


async def create_knowledge_base(user_id: int,
                                name: str,
                                domain: str,
                                sub_domain: str = None) -> int:
    """创建知识库"""
    return vector_store.create_knowledge_base(user_id, name, domain,
                                              sub_domain)


async def get_history(user_id: str) -> str:
    """获取用户历史对话"""
    # 简化实现：返回空历史
    return ""


async def save_interview_record(user_id: str, kb_id: int, scene_type: str,
                                last_question: str, user_answer: str,
                                result: Dict[str, Any]):
    """保存面试记录"""
    # 简化实现：仅打印日志
    print(f"保存面试记录: user_id={user_id}, kb_id={kb_id}, scene_type={scene_type}")
    return True


# 知识库相关路由
@app.post("/api/knowledge-bases")
async def create_kb(user_id: int = Form(...),
                    name: str = Form(...),
                    domain: str = Form(...),
                    sub_domain: Optional[str] = Form(None)):
    """创建知识库"""
    try:
        kb_id = await create_knowledge_base(user_id, name, domain, sub_domain)
        return {"status": "success", "kb_id": kb_id, "message": "知识库创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库创建失败: {str(e)}")


@app.get("/api/knowledge-bases/{user_id}")
async def get_kbs(user_id: int):
    """获取用户的知识库列表"""
    try:
        # 简化实现：返回示例数据
        return {
            "status":
            "success",
            "knowledge_bases": [{
                "id": 1,
                "name": "Python编程",
                "domain": "it",
                "sub_domain": "backend"
            }]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库失败: {str(e)}")


# 文档上传和处理路由
# 文档上传处理已移至 routes/upload.py


@app.get("/api/task/{task_id}")
@limiter.limit("30/minute")
async def get_task_status(request: Request, task_id: str):
    """获取任务状态"""
    try:
        from utils.redis import redis_cache
        task_status = redis_cache.get(f"task_status:{task_id}")

        if not task_status:
            return {
                "status": "unknown",
                "message": "任务未找到或已过期",
                "task_id": task_id
            }

        return {
            "status": task_status["status"],
            "progress": task_status["progress"],
            "message": task_status.get("message", ""),
            "task_id": task_id,
            "error": task_status.get("error", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


# 面试相关路由
@app.post("/api/interview/start")
async def start_interview(kb_id: int, scene_type: str, user_id: str):
    """开始面试"""
    try:
        # 根据场景类型设置相应的角色和主题
        role_map = {
            'it': 'software_engineer',
            'language': 'language_tutor',
            'cert': 'certification_examiner'
        }

        topic_map = {'it': '技术面试', 'language': '小语种口语面试', 'cert': '职业考证面试'}

        role = role_map.get(scene_type, 'software_engineer')
        topic = topic_map.get(scene_type, '技术面试')

        # 获取面试Agent实例
        agent = get_interviewer_agent()

        # 设置面试角色
        agent.set_role(role)

        # 生成初始问题
        initial_response = agent.start_interview(topic)

        return {
            "status": "success",
            "interview_id": f"interview_{os.getpid()}_{time.time()}",
            "initial_response": initial_response,
            "message": "面试已开始"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"面试开始失败: {str(e)}")


@app.post("/api/interview/ask")
def ask_question(user_answer: str):
    """根据用户回答生成下一个问题"""
    try:
        agent = get_interviewer_agent()
        response = agent.ask_question(user_answer)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问题生成失败: {str(e)}")


@app.post("/api/interview/text")
async def interview_text(user_id: str = Form(...),
                         kb_id: int = Form(...),
                         scene_type: str = Form(...),
                         user_answer: str = Form(...),
                         last_question: str = Form(...)):
    """文本面试接口"""
    try:
        # 1. RAG检索
        query_emb = (await embed([last_question]))[0]
        context_docs = vector_store.similarity_search(query_emb, kb_id)
        context = "\n".join([d["content"] for d in context_docs])

        # 2. Agent面试
        history = await get_history(user_id)
        agent = get_interviewer_agent()
        result = agent.run_interview(scene_type, user_answer, last_question,
                                     context, history)

        # 3. 保存记录
        await save_interview_record(user_id, kb_id, scene_type, last_question,
                                    user_answer, result)

        return {
            "status": "success",
            "score": result["score"],
            "follow_up": result["follow_up"],
            "comment": result["comment"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"面试处理失败: {str(e)}")


from agent.interviewer_stream import run_interview_stream, get_full_response


@app.get("/api/interview/stream")
async def interview_stream(user_id: str, kb_id: int, scene_type: str,
                           user_answer: str, last_question: str):
    """流式面试接口（SSE）"""

    async def generate_stream():
        try:
            # 1. RAG检索
            query_emb = (await embed([last_question]))[0]
            context_docs = vector_store.similarity_search(query_emb, kb_id)
            context = "\n".join([d["content"] for d in context_docs])

            # 2. 获取历史对话
            history = await get_history(user_id)

            # 3. 调用真正的流式Agent
            full_response = ""
            async for token in run_interview_stream(scene_type, user_answer,
                                                    context):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                await asyncio.sleep(0.03)  # 控制打字速度

            # 4. 获取评分和评论（简化实现，实际项目中可能需要更复杂的解析）
            # 这里使用辅助函数获取完整解析后的响应
            result = await get_full_response(scene_type, user_answer, context)

            # 5. 保存记录
            await save_interview_record(user_id, kb_id, scene_type,
                                        last_question, user_answer, result)

            # 6. 发送结束信号
            yield f"data: {json.dumps({'type': 'end', 'score': result['score'], 'comment': result['comment']})}\n\n"
        except Exception as e:
            print(f"流式面试错误: {e}")
            yield f"data: {json.dumps({'type': 'token', 'token': '抱歉，系统出错了。'})}\n\n"
            yield f"data: {json.dumps({'type': 'end', 'score': 0, 'comment': f'系统错误: {str(e)}'})}\n\n"

    return StreamingResponse(generate_stream(),
                             media_type="text/event-stream",
                             headers={
                                 "Cache-Control": "no-cache",
                                 "Connection": "keep-alive"
                             })


@app.post("/api/interview/end")
def end_interview():
    """结束面试并生成反馈"""
    try:
        agent = get_interviewer_agent()

        # 结束面试
        closing_response = agent.end_interview()

        # 生成面试反馈
        feedback = agent.generate_feedback()

        # 生成面试报告
        report = report_generator.generate_technical_report(feedback)

        return {
            "status": "success",
            "closing_response": closing_response,
            "feedback": feedback,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"面试结束处理失败: {str(e)}")


# 报告相关路由
@app.post("/api/report/generate")
def generate_report(interview_data: Dict[str, Any]):
    """生成面试报告"""
    try:
        report = report_generator.generate_technical_report(interview_data)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@app.get("/api/report")
async def get_report(user_id: str, domain: str):
    """获取用户的面试报告"""
    try:
        # 简化实现：返回示例报告
        return {
            "status": "success",
            "report": {
                "avg_score": 8.5,
                "weak_points": ["系统设计能力需要加强", "算法基础不够扎实"],
                "progress_tracking": "平均分 8.5，较上次 ↑",
                "real_questions": ["分布式系统设计", "算法优化"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告失败: {str(e)}")


# 运行应用
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
