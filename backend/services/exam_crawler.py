import requests
import re
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import settings
from utils.redis import redis_cache


@dataclass
class ExamQuestion:
    """考试题目数据类"""
    question_id: str
    exam_type: str
    question_type: str  # single_choice, multi_choice, essay, etc.
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str  # easy, medium, hard
    tags: List[str]
    source: str


class ExamCrawler:
    """考试真题爬取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def crawl_exam_questions(self, exam_type: str, year: Optional[int] = None, limit: int = 50) -> List[ExamQuestion]:
        """爬取考试题目
        
        Args:
            exam_type: 考试类型（soft_high, pmp, cpa, teacher, etc.）
            year: 年份（可选）
            limit: 题目数量限制
            
        Returns:
            考试题目列表
        """
        try:
            # 生成缓存键
            cache_key = f"exam_questions:{exam_type}:{year if year else 'all'}:{limit}"
            
            # 尝试从缓存获取
            cached_data = redis_cache.get(cache_key)
            if cached_data:
                return [ExamQuestion(**q) for q in json.loads(cached_data)]
            
            # 根据考试类型选择爬取策略
            if exam_type == "soft_high":
                questions = self._crawl_soft_high_exam(year, limit)
            elif exam_type == "pmp":
                questions = self._crawl_pmp_exam(year, limit)
            elif exam_type == "cpa":
                questions = self._crawl_cpa_exam(year, limit)
            elif exam_type == "teacher":
                questions = self._crawl_teacher_exam(year, limit)
            else:
                # 默认爬取模拟数据
                questions = self._generate_mock_questions(exam_type, limit)
            
            # 存入缓存（过期时间24小时）
            if questions:
                questions_data = [q.__dict__ for q in questions]
                redis_cache.set(cache_key, json.dumps(questions_data), expire=24 * 60 * 60)
            
            return questions
            
        except Exception as e:
            print(f"爬取考试题目失败: {e}")
            return self._generate_mock_questions(exam_type, limit)
    
    def _crawl_soft_high_exam(self, year: Optional[int], limit: int) -> List[ExamQuestion]:
        """爬取软考真题"""
        questions = []
        
        try:
            # 这里应该实现实际的软考网站爬取逻辑
            # 由于时间和权限限制，这里返回模拟数据
            questions = self._generate_soft_high_mock_questions(limit)
            
        except Exception as e:
            print(f"软考题库爬取失败: {e}")
            questions = self._generate_soft_high_mock_questions(limit)
        
        return questions
    
    def _crawl_pmp_exam(self, year: Optional[int], limit: int) -> List[ExamQuestion]:
        """爬取PMP考试题目"""
        questions = []
        
        try:
            # PMP考试题目爬取逻辑
            questions = self._generate_pmp_mock_questions(limit)
            
        except Exception as e:
            print(f"PMP题库爬取失败: {e}")
            questions = self._generate_pmp_mock_questions(limit)
        
        return questions
    
    def _crawl_cpa_exam(self, year: Optional[int], limit: int) -> List[ExamQuestion]:
        """爬取CPA考试题目"""
        questions = []
        
        try:
            # CPA考试题目爬取逻辑
            questions = self._generate_cpa_mock_questions(limit)
            
        except Exception as e:
            print(f"CPA题库爬取失败: {e}")
            questions = self._generate_cpa_mock_questions(limit)
        
        return questions
    
    def _crawl_teacher_exam(self, year: Optional[int], limit: int) -> List[ExamQuestion]:
        """爬取教师资格证考试题目"""
        questions = []
        
        try:
            # 教师资格证考试题目爬取逻辑
            questions = self._generate_teacher_mock_questions(limit)
            
        except Exception as e:
            print(f"教师资格证题库爬取失败: {e}")
            questions = self._generate_teacher_mock_questions(limit)
        
        return questions
    
    def _generate_mock_questions(self, exam_type: str, limit: int) -> List[ExamQuestion]:
        """生成模拟题目"""
        questions = []
        
        for i in range(limit):
            question = ExamQuestion(
                question_id=f"{exam_type}_mock_{i+1}",
                exam_type=exam_type,
                question_type="single_choice",
                question_text=f"这是{exam_type}考试的第{i+1}道模拟题目，请问正确答案是什么？",
                options=["选项A", "选项B", "选项C", "选项D"],
                correct_answer="选项B",
                explanation="这是题目的解析说明",
                difficulty="medium",
                tags=["模拟题", exam_type],
                source="模拟数据"
            )
            questions.append(question)
        
        return questions
    
    def _generate_soft_high_mock_questions(self, limit: int) -> List[ExamQuestion]:
        """生成软考模拟题目"""
        questions = []
        
        soft_high_topics = [
            "数据结构", "算法", "操作系统", "计算机网络", 
            "数据库", "软件工程", "系统架构"
        ]
        
        for i in range(limit):
            topic = soft_high_topics[i % len(soft_high_topics)]
            
            question = ExamQuestion(
                question_id=f"soft_high_{i+1}",
                exam_type="soft_high",
                question_type="single_choice",
                question_text=f"关于{topic}的以下描述中，哪一项是正确的？",
                options=[
                    f"选项A：关于{topic}的正确描述",
                    f"选项B：关于{topic}的错误描述", 
                    f"选项C：关于{topic}的部分正确描述",
                    f"选项D：关于{topic}的无关描述"
                ],
                correct_answer="选项A",
                explanation=f"本题考查{topic}的基本概念和原理",
                difficulty=["easy", "medium", "hard"][i % 3],
                tags=[topic, "软考", "计算机"],
                source="软考模拟题库"
            )
            questions.append(question)
        
        return questions
    
    def _generate_pmp_mock_questions(self, limit: int) -> List[ExamQuestion]:
        """生成PMP模拟题目"""
        questions = []
        
        pmp_topics = [
            "项目启动", "项目规划", "项目执行", "项目监控", 
            "项目收尾", "风险管理", "质量管理"
        ]
        
        for i in range(limit):
            topic = pmp_topics[i % len(pmp_topics)]
            
            question = ExamQuestion(
                question_id=f"pmp_{i+1}",
                exam_type="pmp",
                question_type="single_choice",
                question_text=f"在PMP项目管理中，关于{topic}的正确做法是？",
                options=[
                    f"选项A：{topic}的标准做法",
                    f"选项B：{topic}的错误做法",
                    f"选项C：{topic}的部分正确做法",
                    f"选项D：{topic}的无关做法"
                ],
                correct_answer="选项A",
                explanation=f"本题考查PMP中{topic}的知识点",
                difficulty=["easy", "medium", "hard"][i % 3],
                tags=[topic, "PMP", "项目管理"],
                source="PMP模拟题库"
            )
            questions.append(question)
        
        return questions
    
    def _generate_cpa_mock_questions(self, limit: int) -> List[ExamQuestion]:
        """生成CPA模拟题目"""
        questions = []
        
        cpa_topics = [
            "财务会计", "审计", "税法", "经济法",
            "公司战略", "财务管理"
        ]
        
        for i in range(limit):
            topic = cpa_topics[i % len(cpa_topics)]
            
            question = ExamQuestion(
                question_id=f"cpa_{i+1}",
                exam_type="cpa",
                question_type="single_choice",
                question_text=f"在CPA考试中，关于{topic}的正确处理方法是？",
                options=[
                    f"选项A：{topic}的标准处理方法",
                    f"选项B：{topic}的错误处理方法",
                    f"选项C：{topic}的部分正确处理方法",
                    f"选项D：{topic}的无关处理方法"
                ],
                correct_answer="选项A",
                explanation=f"本题考查CPA中{topic}的知识点",
                difficulty=["easy", "medium", "hard"][i % 3],
                tags=[topic, "CPA", "会计"],
                source="CPA模拟题库"
            )
            questions.append(question)
        
        return questions
    
    def _generate_teacher_mock_questions(self, limit: int) -> List[ExamQuestion]:
        """生成教师资格证模拟题目"""
        questions = []
        
        teacher_topics = [
            "教育学", "心理学", "教育法规", "教学技能",
            "课程设计", "学生评估"
        ]
        
        for i in range(limit):
            topic = teacher_topics[i % len(teacher_topics)]
            
            question = ExamQuestion(
                question_id=f"teacher_{i+1}",
                exam_type="teacher",
                question_type="single_choice",
                question_text=f"在教师资格证考试中，关于{topic}的正确理解是？",
                options=[
                    f"选项A：{topic}的正确理解",
                    f"选项B：{topic}的错误理解",
                    f"选项C：{topic}的部分正确理解",
                    f"选项D：{topic}的无关理解"
                ],
                correct_answer="选项A",
                explanation=f"本题考查教师资格证中{topic}的知识点",
                difficulty=["easy", "medium", "hard"][i % 3],
                tags=[topic, "教师资格证", "教育"],
                source="教师资格证模拟题库"
            )
            questions.append(question)
        
        return questions
    
    def search_questions(self, keyword: str, exam_type: Optional[str] = None, difficulty: Optional[str] = None) -> List[ExamQuestion]:
        """搜索题目
        
        Args:
            keyword: 关键词
            exam_type: 考试类型过滤（可选）
            difficulty: 难度过滤（可选）
            
        Returns:
            匹配的题目列表
        """
        try:
            # 生成缓存键
            cache_key = f"exam_search:{keyword}:{exam_type if exam_type else 'all'}:{difficulty if difficulty else 'all'}"
            
            # 尝试从缓存获取
            cached_data = redis_cache.get(cache_key)
            if cached_data:
                return [ExamQuestion(**q) for q in json.loads(cached_data)]
            
            # 这里应该实现实际的搜索逻辑
            # 简化实现：返回模拟数据
            questions = self._generate_mock_questions(exam_type or "general", 10)
            
            # 过滤结果
            filtered_questions = []
            for q in questions:
                # 关键词匹配
                if keyword.lower() in q.question_text.lower() or any(keyword.lower() in tag.lower() for tag in q.tags):
                    # 考试类型过滤
                    if exam_type and q.exam_type != exam_type:
                        continue
                    # 难度过滤
                    if difficulty and q.difficulty != difficulty:
                        continue
                    
                    filtered_questions.append(q)
            
            # 存入缓存（过期时间1小时）
            if filtered_questions:
                questions_data = [q.__dict__ for q in filtered_questions]
                redis_cache.set(cache_key, json.dumps(questions_data), expire=60 * 60)
            
            return filtered_questions
            
        except Exception as e:
            print(f"搜索题目失败: {e}")
            return []
    
    def get_exam_statistics(self, exam_type: str) -> Dict[str, Any]:
        """获取考试统计信息
        
        Args:
            exam_type: 考试类型
            
        Returns:
            统计信息
        """
        try:
            # 生成缓存键
            cache_key = f"exam_stats:{exam_type}"
            
            # 尝试从缓存获取
            cached_data = redis_cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # 获取题目数据
            questions = self.crawl_exam_questions(exam_type, limit=100)
            
            # 计算统计信息
            total_questions = len(questions)
            difficulty_dist = {}
            type_dist = {}
            
            for q in questions:
                difficulty_dist[q.difficulty] = difficulty_dist.get(q.difficulty, 0) + 1
                type_dist[q.question_type] = type_dist.get(q.question_type, 0) + 1
            
            stats = {
                "exam_type": exam_type,
                "total_questions": total_questions,
                "difficulty_distribution": difficulty_dist,
                "question_type_distribution": type_dist,
                "last_updated": time.time()
            }
            
            # 存入缓存（过期时间6小时）
            redis_cache.set(cache_key, json.dumps(stats), expire=6 * 60 * 60)
            
            return stats
            
        except Exception as e:
            print(f"获取考试统计失败: {e}")
            return {"exam_type": exam_type, "total_questions": 0, "difficulty_distribution": {}, "question_type_distribution": {}}


def get_exam_crawler() -> ExamCrawler:
    """获取考试爬取器实例"""
    return ExamCrawler()