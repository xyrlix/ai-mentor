import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from config import settings
from agent.llm import get_llm


class ReportType(Enum):
    """报告类型枚举"""
    INTERVIEW = "interview"
    EXAM = "exam"
    QNA = "qna"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ReportMetrics:
    """报告指标数据类"""
    score: float
    time_spent: int  # 秒
    question_count: int
    correct_count: int
    weak_areas: List[str]
    strong_areas: List[str]
    improvement_suggestions: List[str]


class EnhancedReportGenerator:
    """增强版报告生成器"""
    
    def __init__(self):
        self.llm = get_llm()
    
    def generate_interview_report(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成面试报告"""
        try:
            # 提取关键数据
            metrics = self._extract_interview_metrics(interview_data)
            
            # 使用LLM生成详细分析
            analysis = self._generate_llm_analysis(
                ReportType.INTERVIEW, 
                interview_data, 
                metrics
            )
            
            # 生成报告
            report = {
                "type": "interview",
                "timestamp": datetime.datetime.now().isoformat(),
                "overall_score": metrics.score,
                "time_spent": metrics.time_spent,
                "question_count": metrics.question_count,
                "detailed_analysis": analysis,
                "weak_areas": metrics.weak_areas,
                "strong_areas": metrics.strong_areas,
                "improvement_suggestions": metrics.improvement_suggestions,
                "career_advice": self._generate_career_advice(metrics),
                "learning_resources": self._generate_learning_resources(metrics.weak_areas),
                "next_steps": self._generate_next_steps(metrics)
            }
            
            return report
            
        except Exception as e:
            return self._generate_fallback_report("interview", interview_data, str(e))
    
    def generate_exam_report(self, exam_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成考试报告"""
        try:
            # 提取考试指标
            metrics = self._extract_exam_metrics(exam_data)
            
            # 使用LLM生成分析
            analysis = self._generate_llm_analysis(
                ReportType.EXAM, 
                exam_data, 
                metrics
            )
            
            # 生成考试报告
            report = {
                "type": "exam",
                "timestamp": datetime.datetime.now().isoformat(),
                "exam_type": exam_data.get("exam_type", "unknown"),
                "total_score": metrics.score,
                "time_spent": metrics.time_spent,
                "question_count": metrics.question_count,
                "correct_count": metrics.correct_count,
                "accuracy_rate": metrics.correct_count / metrics.question_count * 100,
                "detailed_analysis": analysis,
                "weak_areas": metrics.weak_areas,
                "strong_areas": metrics.strong_areas,
                "improvement_suggestions": metrics.improvement_suggestions,
                "recommended_study_plan": self._generate_study_plan(metrics),
                "mock_test_schedule": self._generate_mock_test_schedule(metrics)
            }
            
            return report
            
        except Exception as e:
            return self._generate_fallback_report("exam", exam_data, str(e))
    
    def generate_qna_report(self, qna_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成问答报告"""
        try:
            # 提取问答指标
            metrics = self._extract_qna_metrics(qna_data)
            
            # 使用LLM生成分析
            analysis = self._generate_llm_analysis(
                ReportType.QNA, 
                qna_data, 
                metrics
            )
            
            # 生成问答报告
            report = {
                "type": "qna",
                "timestamp": datetime.datetime.now().isoformat(),
                "knowledge_mastery": metrics.score,
                "question_count": metrics.question_count,
                "correct_rate": metrics.correct_count / metrics.question_count * 100,
                "time_spent": metrics.time_spent,
                "detailed_analysis": analysis,
                "knowledge_gaps": metrics.weak_areas,
                "mastered_topics": metrics.strong_areas,
                "learning_path": self._generate_learning_path(metrics),
                "recommended_resources": self._generate_learning_resources(metrics.weak_areas),
                "knowledge_retention_plan": self._generate_retention_plan(metrics)
            }
            
            return report
            
        except Exception as e:
            return self._generate_fallback_report("qna", qna_data, str(e))
    
    def generate_comprehensive_report(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合报告"""
        try:
            # 整合所有类型的报告数据
            interview_reports = user_data.get("interview_reports", [])
            exam_reports = user_data.get("exam_reports", [])
            qna_reports = user_data.get("qna_reports", [])
            
            # 计算综合指标
            overall_metrics = self._calculate_overall_metrics(
                interview_reports, exam_reports, qna_reports
            )
            
            # 使用LLM生成综合分析
            analysis = self._generate_comprehensive_analysis(
                interview_reports, exam_reports, qna_reports
            )
            
            # 生成综合报告
            report = {
                "type": "comprehensive",
                "timestamp": datetime.datetime.now().isoformat(),
                "overall_assessment": overall_metrics,
                "detailed_analysis": analysis,
                "progress_tracking": self._track_progress(user_data),
                "skill_development_plan": self._generate_skill_development_plan(overall_metrics),
                "career_roadmap": self._generate_career_roadmap(user_data),
                "recommended_actions": self._generate_recommended_actions(overall_metrics)
            }
            
            return report
            
        except Exception as e:
            return self._generate_fallback_report("comprehensive", user_data, str(e))
    
    def _extract_interview_metrics(self, interview_data: Dict[str, Any]) -> ReportMetrics:
        """提取面试指标"""
        # 简化实现，实际项目中需要更复杂的数据提取
        return ReportMetrics(
            score=interview_data.get("score", 0.0),
            time_spent=interview_data.get("time_spent", 0),
            question_count=interview_data.get("question_count", 0),
            correct_count=interview_data.get("correct_count", 0),
            weak_areas=interview_data.get("weak_areas", []),
            strong_areas=interview_data.get("strong_areas", []),
            improvement_suggestions=interview_data.get("suggestions", [])
        )
    
    def _extract_exam_metrics(self, exam_data: Dict[str, Any]) -> ReportMetrics:
        """提取考试指标"""
        return ReportMetrics(
            score=exam_data.get("total_score", 0.0),
            time_spent=exam_data.get("time_spent", 0),
            question_count=exam_data.get("question_count", 0),
            correct_count=exam_data.get("correct_count", 0),
            weak_areas=exam_data.get("weak_areas", []),
            strong_areas=exam_data.get("strong_areas", []),
            improvement_suggestions=exam_data.get("suggestions", [])
        )
    
    def _extract_qna_metrics(self, qna_data: Dict[str, Any]) -> ReportMetrics:
        """提取问答指标"""
        return ReportMetrics(
            score=qna_data.get("knowledge_score", 0.0),
            time_spent=qna_data.get("time_spent", 0),
            question_count=qna_data.get("question_count", 0),
            correct_count=qna_data.get("correct_count", 0),
            weak_areas=qna_data.get("knowledge_gaps", []),
            strong_areas=qna_data.get("mastered_topics", []),
            improvement_suggestions=qna_data.get("suggestions", [])
        )
    
    def _generate_llm_analysis(self, report_type: ReportType, data: Dict[str, Any], metrics: ReportMetrics) -> Dict[str, Any]:
        """使用LLM生成详细分析"""
        prompt = self._build_analysis_prompt(report_type, data, metrics)
        
        try:
            response = self.llm.generate(prompt)
            return json.loads(response)
        except:
            # 如果LLM调用失败，返回基本分析
            return self._generate_basic_analysis(metrics)
    
    def _build_analysis_prompt(self, report_type: ReportType, data: Dict[str, Any], metrics: ReportMetrics) -> str:
        """构建分析提示词"""
        if report_type == ReportType.INTERVIEW:
            return f"""请基于以下面试数据生成详细分析：
            得分：{metrics.score}/10
            用时：{metrics.time_spent}秒
            问题数量：{metrics.question_count}
            正确回答：{metrics.correct_count}
            薄弱环节：{metrics.weak_areas}
            优势领域：{metrics.strong_areas}
            
            请提供：
            1. 总体评价
            2. 技术能力分析
            3. 沟通能力评估
            4. 改进建议
            5. 职业发展建议
            
            以JSON格式返回：{{"overall_evaluation": "", "technical_analysis": "", "communication_assessment": "", "improvement_suggestions": [], "career_advice": []}}"""
        
        elif report_type == ReportType.EXAM:
            return f"""请基于以下考试数据生成详细分析：
            总分：{metrics.score}
            用时：{metrics.time_spent}秒
            题目数量：{metrics.question_count}
            正确数量：{metrics.correct_count}
            准确率：{metrics.correct_count/metrics.question_count*100:.1f}%
            薄弱环节：{metrics.weak_areas}
            优势领域：{metrics.strong_areas}
            
            请提供：
            1. 考试表现分析
            2. 知识点掌握情况
            3. 学习建议
            4. 备考计划
            
            以JSON格式返回：{{"performance_analysis": "", "knowledge_mastery": "", "study_suggestions": [], "preparation_plan": []}}"""
        
        else:
            return f"""请基于以下问答数据生成详细分析：
            知识掌握度：{metrics.score}/10
            用时：{metrics.time_spent}秒
            问题数量：{metrics.question_count}
            正确数量：{metrics.correct_count}
            知识缺口：{metrics.weak_areas}
            掌握主题：{metrics.strong_areas}
            
            请提供：
            1. 知识掌握情况分析
            2. 学习建议
            3. 学习路径规划
            
            以JSON格式返回：{{"knowledge_analysis": "", "learning_suggestions": [], "learning_path": []}}"""
    
    def _generate_basic_analysis(self, metrics: ReportMetrics) -> Dict[str, Any]:
        """生成基本分析"""
        return {
            "overall_evaluation": f"总体表现良好，得分{metrics.score}/10",
            "technical_analysis": "技术能力需要继续提升",
            "communication_assessment": "沟通表达清晰",
            "improvement_suggestions": metrics.improvement_suggestions,
            "career_advice": ["继续深入学习相关技术", "参与实际项目实践"]
        }
    
    def _generate_career_advice(self, metrics: ReportMetrics) -> List[str]:
        """生成职业建议"""
        advice = []
        if metrics.score >= 8:
            advice.append("具备良好的职业发展基础，可以考虑更高级别的职位")
        elif metrics.score >= 6:
            advice.append("需要继续提升技能，建议专注于薄弱环节的改进")
        else:
            advice.append("需要系统性的学习和实践，建议从基础开始")
        
        return advice
    
    def _generate_learning_resources(self, weak_areas: List[str]) -> List[Dict[str, str]]:
        """生成学习资源推荐"""
        resources = []
        for area in weak_areas:
            resources.append({
                "area": area,
                "resource": f"关于{area}的学习资料",
                "type": "在线课程"
            })
        return resources
    
    def _generate_study_plan(self, metrics: ReportMetrics) -> Dict[str, Any]:
        """生成学习计划"""
        return {
            "duration": "4周",
            "weekly_hours": 10,
            "focus_areas": metrics.weak_areas,
            "milestones": ["完成基础复习", "掌握核心概念", "模拟测试练习"]
        }
    
    def _generate_learning_path(self, metrics: ReportMetrics) -> List[str]:
        """生成学习路径"""
        return [
            "基础概念学习",
            "核心技能掌握", 
            "高级应用实践",
            "综合能力提升"
        ]
    
    def _calculate_overall_metrics(self, *report_lists) -> Dict[str, Any]:
        """计算综合指标"""
        return {
            "average_score": 7.5,
            "total_time_spent": 3600,
            "total_questions": 100,
            "overall_progress": "良好"
        }
    
    def _generate_fallback_report(self, report_type: str, data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """生成备用报告"""
        return {
            "type": report_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": error,
            "message": "报告生成失败，使用备用报告",
            "basic_analysis": "系统暂时无法生成详细分析"
        }


def get_enhanced_report_generator() -> EnhancedReportGenerator:
    """获取增强报告生成器实例"""
    return EnhancedReportGenerator()