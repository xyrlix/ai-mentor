from fastapi import APIRouter, HTTPException, Form, Query
from typing import List, Dict, Any, Optional
import json
import time

# 导入相关模块
from agent.exam_agent import get_exam_agent
from utils.redis import redis_cache

router = APIRouter(prefix="/api/exam", tags=["考试模拟"])

# 获取考试Agent实例
exam_agent = get_exam_agent()


@router.get("/types")
async def get_exam_types() -> Dict[str, Any]:
    """获取支持的考试类型"""
    try:
        exam_types = exam_agent.get_exam_types()
        return {
            "status": "success",
            "exam_types": exam_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取考试类型失败: {str(e)}")


@router.post("/generate-question")
async def generate_question(
    exam_type: str = Form(..., description="考试类型"),
    question_type: str = Form(..., description="题型"),
    topic: str = Form(..., description="主题"),
    difficulty: str = Form("中等", description="难度"),
    context: str = Form("", description="上下文信息")
) -> Dict[str, Any]:
    """生成考试试题"""
    try:
        question = exam_agent.generate_question(
            exam_type=exam_type,
            question_type=question_type,
            topic=topic,
            difficulty=difficulty,
            context=context
        )
        
        if 'error' in question:
            raise HTTPException(status_code=400, detail=question['error'])
        
        return {
            "status": "success",
            "question": question
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成试题失败: {str(e)}")


@router.post("/generate-question-set")
async def generate_question_set(
    exam_type: str = Form(..., description="考试类型"),
    topic: str = Form(..., description="主题"),
    count: int = Form(10, description="试题数量"),
    difficulty: str = Form("中等", description="难度"),
    context: str = Form("", description="上下文信息")
) -> Dict[str, Any]:
    """生成试题集"""
    try:
        questions = exam_agent.generate_question_set(
            exam_type=exam_type,
            topic=topic,
            count=count,
            difficulty=difficulty,
            context=context
        )
        
        return {
            "status": "success",
            "exam_type": exam_type,
            "topic": topic,
            "question_count": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成试题集失败: {str(e)}")


@router.post("/evaluate-answer")
async def evaluate_answer(
    question: str = Form(..., description="题目"),
    correct_answer: str = Form(..., description="标准答案"),
    user_answer: str = Form(..., description="考生答案")
) -> Dict[str, Any]:
    """评估答题"""
    try:
        evaluation = exam_agent.evaluate_answer(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer
        )
        
        return {
            "status": "success",
            "evaluation": evaluation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估答题失败: {str(e)}")


@router.post("/simulate-exam")
async def simulate_exam(
    exam_type: str = Form(..., description="考试类型"),
    topic: str = Form(..., description="主题"),
    question_count: int = Form(20, description="题目数量"),
    time_limit: int = Form(120, description="时间限制（分钟）")
) -> Dict[str, Any]:
    """模拟考试"""
    try:
        exam_info = exam_agent.simulate_exam(
            exam_type=exam_type,
            topic=topic,
            question_count=question_count,
            time_limit=time_limit
        )
        
        if 'error' in exam_info:
            raise HTTPException(status_code=400, detail=exam_info['error'])
        
        # 生成考试ID
        exam_id = f"exam_{int(time.time())}_{exam_type}"
        
        # 保存考试信息到缓存
        exam_info['exam_id'] = exam_id
        redis_cache.set(f"exam:{exam_id}", json.dumps(exam_info), expire=3600)  # 1小时过期
        
        return {
            "status": "success",
            "exam_id": exam_id,
            "exam_info": exam_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模拟考试失败: {str(e)}")


@router.post("/submit-exam")
async def submit_exam(
    exam_id: str = Form(..., description="考试ID"),
    answers: str = Form(..., description="考生答案（JSON格式）")
) -> Dict[str, Any]:
    """提交考试答案"""
    try:
        # 获取考试信息
        exam_data = redis_cache.get(f"exam:{exam_id}")
        if not exam_data:
            raise HTTPException(status_code=404, detail="考试不存在或已过期")
        
        exam_info = json.loads(exam_data)
        questions = exam_info.get('questions', [])
        
        # 解析答案
        try:
            user_answers = json.loads(answers)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="答案格式错误")
        
        # 计算成绩
        score_report = exam_agent.calculate_score(user_answers, questions)
        
        # 保存成绩记录
        exam_record = {
            'exam_id': exam_id,
            'exam_type': exam_info.get('exam_type'),
            'topic': exam_info.get('topic'),
            'user_answers': user_answers,
            'score_report': score_report,
            'submitted_at': exam_agent.get_current_time()
        }
        
        # 生成记录ID
        record_id = f"record_{int(time.time())}"
        redis_cache.set(f"exam_record:{record_id}", json.dumps(exam_record), expire=86400)  # 24小时过期
        
        return {
            "status": "success",
            "record_id": record_id,
            "score_report": score_report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交考试失败: {str(e)}")


@router.get("/exam-info/{exam_id}")
async def get_exam_info(exam_id: str) -> Dict[str, Any]:
    """获取考试信息"""
    try:
        exam_data = redis_cache.get(f"exam:{exam_id}")
        if not exam_data:
            raise HTTPException(status_code=404, detail="考试不存在或已过期")
        
        exam_info = json.loads(exam_data)
        
        return {
            "status": "success",
            "exam_info": exam_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取考试信息失败: {str(e)}")


@router.get("/exam-record/{record_id}")
async def get_exam_record(record_id: str) -> Dict[str, Any]:
    """获取考试记录"""
    try:
        record_data = redis_cache.get(f"exam_record:{record_id}")
        if not record_data:
            raise HTTPException(status_code=404, detail="考试记录不存在")
        
        exam_record = json.loads(record_data)
        
        return {
            "status": "success",
            "exam_record": exam_record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取考试记录失败: {str(e)}")


@router.get("/user-records/{user_id}")
async def get_user_exam_records(
    user_id: str,
    limit: int = Query(10, description="返回记录数量")
) -> Dict[str, Any]:
    """获取用户的考试记录"""
    try:
        # 简化实现：返回空列表
        # 实际项目中应该从数据库获取用户的考试记录
        
        return {
            "status": "success",
            "user_id": user_id,
            "records": [],
            "total_count": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户记录失败: {str(e)}")


@router.post("/practice-mode")
async def practice_mode(
    exam_type: str = Form(..., description="考试类型"),
    topic: str = Form(..., description="主题"),
    question_count: int = Form(5, description="题目数量")
) -> Dict[str, Any]:
    """练习模式 - 逐题练习"""
    try:
        # 生成练习题目
        questions = exam_agent.generate_question_set(
            exam_type=exam_type,
            topic=topic,
            count=question_count
        )
        
        # 生成练习ID
        practice_id = f"practice_{int(time.time())}"
        
        # 保存练习信息
        practice_info = {
            'practice_id': practice_id,
            'exam_type': exam_type,
            'topic': topic,
            'questions': questions,
            'current_question': 0,
            'user_answers': {},
            'started_at': exam_agent.get_current_time()
        }
        
        redis_cache.set(f"practice:{practice_id}", json.dumps(practice_info), expire=7200)  # 2小时过期
        
        # 返回第一题
        current_question = questions[0] if questions else None
        
        return {
            "status": "success",
            "practice_id": practice_id,
            "current_question": current_question,
            "question_count": len(questions),
            "current_index": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动练习模式失败: {str(e)}")


@router.post("/next-question")
async def next_question(
    practice_id: str = Form(..., description="练习ID"),
    user_answer: str = Form("", description="用户答案")
) -> Dict[str, Any]:
    """下一题"""
    try:
        # 获取练习信息
        practice_data = redis_cache.get(f"practice:{practice_id}")
        if not practice_data:
            raise HTTPException(status_code=404, detail="练习不存在或已过期")
        
        practice_info = json.loads(practice_data)
        questions = practice_info.get('questions', [])
        current_index = practice_info.get('current_question', 0)
        
        # 保存当前答案
        if user_answer:
            practice_info['user_answers'][current_index + 1] = user_answer
        
        # 下一题
        current_index += 1
        
        if current_index >= len(questions):
            # 练习完成，计算成绩
            score_report = exam_agent.calculate_score(practice_info['user_answers'], questions)
            
            # 保存最终记录
            practice_info['current_question'] = current_index
            practice_info['completed_at'] = exam_agent.get_current_time()
            practice_info['score_report'] = score_report
            
            redis_cache.set(f"practice:{practice_id}", json.dumps(practice_info), expire=3600)
            
            return {
                "status": "completed",
                "practice_id": practice_id,
                "score_report": score_report,
                "total_questions": len(questions)
            }
        
        # 更新练习信息
        practice_info['current_question'] = current_index
        redis_cache.set(f"practice:{practice_id}", json.dumps(practice_info), expire=7200)
        
        # 返回下一题
        current_question = questions[current_index]
        
        return {
            "status": "success",
            "practice_id": practice_id,
            "current_question": current_question,
            "question_count": len(questions),
            "current_index": current_index
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取下一题失败: {str(e)}")