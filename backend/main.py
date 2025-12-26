from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
import time
import json
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
    
    # 异步加载嵌入模型，避免阻塞启动
    from rag.embedding import get_embedding_model
    import asyncio
    asyncio.create_task(load_embedding_model())
    
    print("启动完成")


async def load_embedding_model():
    """异步加载嵌入模型"""
    try:
        print("开始异步加载嵌入模型...")
        from rag.embedding import get_embedding_model
        embedding_model = get_embedding_model()
        # 调用模型的_embed方法触发实际加载
        await asyncio.to_thread(embedding_model.embed_query, "测试加载")
        print("嵌入模型异步加载完成")
    except Exception as e:
        print(f"嵌入模型异步加载失败: {e}")
        # 继续运行，模型会在首次使用时重新尝试加载


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


class InterviewStartRequest(BaseModel):
    kb_id: int
    scene_type: str = "it"
    user_id: str = "default_user"


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
async def start_interview(request_data: InterviewStartRequest):
    """开始面试"""
    print("1. 进入 start_interview 函数")
    try:
        # 记录请求数据
        print(f"2. 收到面试开始请求: {request_data.model_dump_json()}")
        
        kb_id = request_data.kb_id
        scene_type = request_data.scene_type
        user_id = request_data.user_id
        
        print(f"3. 面试开始请求参数: kb_id={kb_id}, scene_type={scene_type}, user_id={user_id}")
        
        # 验证参数
        if not isinstance(kb_id, int):
            print(f"面试请求失败: kb_id 必须是整数, 实际类型: {type(kb_id)}")
            raise HTTPException(status_code=400, detail="kb_id must be an integer")
            
        if not kb_id:
            print(f"面试请求失败: kb_id 为空")
            raise HTTPException(status_code=422, detail="kb_id is required")
            
        if not isinstance(scene_type, str):
            print(f"面试请求失败: scene_type 必须是字符串, 实际类型: {type(scene_type)}")
            raise HTTPException(status_code=400, detail="scene_type must be a string")
            
        if scene_type not in ['it', 'language', 'cert']:
            print(f"面试请求失败: scene_type 不在允许的范围内, 实际值: {scene_type}")
            raise HTTPException(status_code=400, detail="scene_type must be one of ['it', 'language', 'cert']")
            
        if not isinstance(user_id, str):
            print(f"面试请求失败: user_id 必须是字符串, 实际类型: {type(user_id)}")
            raise HTTPException(status_code=400, detail="user_id must be a string")
        
        # 根据场景类型设置相应的角色和主题
        role_map = {
            'it': 'software_engineer',
            'language': 'frontend_engineer',  # 语言面试使用前端工程师模板，可以适配
            'cert': 'product_manager'  # 认证考试使用产品经理模板，考察综合能力
        }

        topic_map = {'it': '技术面试', 'language': '小语种口语面试', 'cert': '职业考证面试'}

        role = role_map.get(scene_type, 'software_engineer')
        topic = topic_map.get(scene_type, '技术面试')

        print(f"4. 场景类型: {scene_type}, 角色: {role}, 主题: {topic}")

        # 获取面试Agent实例
        print("5. 开始获取面试Agent实例")
        agent = get_interviewer_agent()
        print("6. 面试Agent实例获取成功")

        # 设置面试角色
        try:
            print(f"7. 设置面试角色: {role}")
            agent.set_role(role)
            print(f"8. 面试角色设置成功: {role}")
        except ValueError as e:
            print(f"设置面试角色失败: {e}")
            raise HTTPException(status_code=400, detail=f"角色设置失败: {str(e)}")

        # 生成基于RAG的初始问题
        print("9. 开始生成基于RAG的初始问题")
        try:
            # RAG检索与场景类型相关的内容
            print(f"10. 开始RAG检索: kb_id={kb_id}, query={topic} 常见面试问题, scene_type={scene_type}")
            initial_context = await retrieve_relevant_content(kb_id, f"{topic} 常见面试问题", scene_type)
            print(f"11. RAG检索完成，context长度: {len(initial_context) if initial_context else 0}")
            print(f"12. 初始上下文内容: {initial_context}")
            
            # 如果有RAG检索到的内容，生成基于内容的初始问题
            if initial_context and initial_context != "无相关文档上下文":
                print(f"13. 开始生成基于RAG内容的初始问题")
                initial_response = ""
                # 直接使用RAG内容生成第一个问题，不使用硬编码的欢迎语
                async for token in run_interview_stream(scene_type, "", initial_context, None):
                    initial_response += token
                    if len(initial_response) > 200:  # 限制初始问题长度
                        break
                print(f"14. RAG初始问题生成完成: {initial_response}")
            else:
                # 如果没有检索到内容，使用默认的初始问题
                print(f"15. 没有检索到相关内容，使用默认初始问题")
                initial_response = f"欢迎参加{topic}！首先，请简单介绍一下你的相关背景和经验。"
                    
        except ValueError as e:
            print(f"生成初始问题失败(400错误): {e}")
            raise HTTPException(status_code=400, detail=f"初始问题生成失败: {str(e)}")
        except Exception as e:
            print(f"RAG检索或问题生成失败: {e}")
            import traceback
            traceback.print_exc()
            initial_response = f"欢迎参加{topic}！首先，请简单介绍一下你的相关背景和经验。"

        print(f"16. 初始问题生成完成: {initial_response}")
        
        response_data = {
            "status": "success",
            "interview_id": f"interview_{os.getpid()}_{time.time()}",
            "initial_response": initial_response,
            "message": "面试已开始"
        }
        
        print(f"17. 返回响应数据: {response_data}")
        return response_data
    except ValueError as e:
        print(f"18. ValueError 异常: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"19. 其他异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"面试开始失败: {str(e)}")
    finally:
        print("20. 退出 start_interview 函数")


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
        print(f"进行RAG检索，知识库ID: {kb_id}, 查询: {last_question}, 场景类型: {scene_type}")
        context = await retrieve_relevant_content(kb_id, last_question, scene_type)
        print(f"RAG检索到的上下文: {context[:100]}..." if context else "RAG未检索到上下文")

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
from rag.embedding import get_embedding_model
from rag.vector_store import get_vector_store


async def retrieve_relevant_content(kb_id: int, query: str, scene_type: str) -> str:
    """RAG检索相关文档内容"""
    try:
        # 获取embedding模型和向量存储
        embedding_model = get_embedding_model()
        vector_store = get_vector_store()
        
        # 生成查询向量
        query_embedding = embedding_model.embed_query(query)
        
        # 检索相关文档（根据场景类型调整检索数量）
        top_k = 5 if scene_type == 'it' else 3  # IT技术面试需要更多上下文
        context_docs = vector_store.similarity_search(query_embedding, kb_id, top_k=top_k)
        
        # 组合上下文内容
        context_parts = []
        for i, doc in enumerate(context_docs):
            context_parts.append(f"文档片段{i+1}:\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        print(f"RAG检索到 {len(context_docs)} 个相关文档片段")
        return context
        
    except Exception as e:
        print(f"RAG检索失败: {e}")
        return "无相关文档上下文"


@app.get("/api/interview/stream")
async def interview_stream(user_id: str, kb_id: int, scene_type: str,
                           user_answer: str, last_question: str = ""):
    """流式面试接口（SSE）"""

    async def generate_stream():
        try:
            nonlocal last_question  # 声明last_question为外部函数变量
            print(f"流式面试请求: user_id={user_id}, kb_id={kb_id}, scene_type={scene_type}")
            print(f"用户回答: {user_answer}")
            
            # 限制 last_question 长度以避免 URL 过长
            if len(last_question) > 200:
                last_question = last_question[:200] + "..."
                print(f"截断过长的问题: {last_question}")
            
            print(f"上一个问题: {last_question}")
            
            # 1. RAG检索相关文档内容作为上下文
            try:
                # 使用上一个问题进行检索，以获取与当前面试主题相关的上下文
                context = await retrieve_relevant_content(kb_id, last_question, scene_type)
                print(f"RAG检索到的context长度: {len(context) if context else 0}")
            except Exception as e:
                print(f"RAG检索失败: {e}")
                context = "无特定上下文"
            print("使用简化的上下文进行流式响应")
            
            # 2. 调用流式Agent
            print(f"开始流式调用: scene_type={scene_type}, user_answer={user_answer}")
            full_response = ""
            token_count = 0
            
            try:
                async for token in run_interview_stream(scene_type, user_answer, context, last_question):
                    full_response += token
                    token_count += 1
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                    await asyncio.sleep(0.05)  # 控制打字速度
                    if token_count > 200:  # 防止无限循环
                        break
                
                print(f"流式调用成功: 生成了 {token_count} 个 tokens")
            except Exception as e:
                print(f"流式调用失败: {e}")
                # 如果流式失败，发送错误消息
                error_msg = "抱歉，系统遇到了一些问题。让我们继续下一个问题吧。"
                for char in error_msg:
                    yield f"data: {json.dumps({'type': 'token', 'token': char})}\n\n"
                    await asyncio.sleep(0.05)
                full_response = error_msg
                token_count = len(error_msg)

            # 3. 保存记录（简化版）
            try:
                result = {
                    'score': 7.0 if len(user_answer) > 10 else 5.0,
                    'follow_up': full_response,
                    'comment': '回答已收到，继续对话'
                }
                await save_interview_record(user_id, kb_id, scene_type,
                                        last_question, user_answer, result)
                print(f"记录保存成功")
            except Exception as e:
                print(f"保存记录失败: {e}")

            # 4. 发送结束信号
            final_score = 7.0 if len(user_answer) > 10 else 5.0
            yield f"data: {json.dumps({'type': 'end', 'score': final_score, 'comment': '对话继续进行中'})}\n\n"
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
        logger.info("开始处理面试结束请求")
        
        agent = get_interviewer_agent()
        logger.info("获取面试Agent实例成功")

        # 结束面试
        logger.info("开始执行结束面试流程")
        closing_response = agent.end_interview()
        logger.info("面试结束流程执行成功")

        # 生成面试反馈
        logger.info("开始生成面试反馈")
        feedback = agent.generate_feedback()
        logger.info("面试反馈生成成功")

        # 生成面试报告
        logger.info("开始生成面试报告")
        report = report_generator.generate_technical_report(feedback)
        logger.info("面试报告生成成功")

        logger.info("面试结束处理完成，返回结果")
        return {
            "status": "success",
            "closing_response": closing_response,
            "feedback": feedback,
            "report": report
        }
    except Exception as e:
        logger.error(f"面试结束处理失败: {str(e)}")
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
