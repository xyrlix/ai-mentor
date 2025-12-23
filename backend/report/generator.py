from typing import List, Dict, Any
from datetime import datetime
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

# 创建数据库会话
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ReportGenerator:
    """面试报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_interview_report(
            self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成面试报告
        
        Args:
            interview_data: 面试数据，包含面试历史、反馈等
        
        Returns:
            结构化的面试报告
        """
        # 提取面试数据
        interview_history = interview_data.get('interview_history', [])
        feedback = interview_data.get('feedback', '')
        role = interview_data.get('role', '')
        topic = interview_data.get('topic', '')

        # 计算面试时长
        if len(interview_history) >= 2:
            # 简单计算：每个回合平均2分钟
            interview_duration = len(interview_history) * 2
        else:
            interview_duration = 0

        # 统计问答数量
        question_count = 0
        answer_count = 0
        for item in interview_history:
            if item['speaker'] == 'interviewer':
                question_count += 1
            else:
                answer_count += 1

        # 生成报告
        report = {
            'report_id':
            self._generate_report_id(),
            'generated_at':
            self.current_time,
            'interview_role':
            role,
            'interview_topic':
            topic,
            'interview_duration':
            interview_duration,
            'question_count':
            question_count,
            'answer_count':
            answer_count,
            'interview_history':
            interview_history,
            'feedback':
            feedback,
            'score':
            self._extract_score(feedback),
            'conclusion':
            self._extract_conclusion(feedback),
            'improvement_suggestions':
            self._extract_improvement_suggestions(feedback)
        }

        return report

    def generate_report(self, user_id: int, domain: str) -> Dict[str, Any]:
        """根据用户ID和领域生成面试报告
        
        Args:
            user_id: 用户ID
            domain: 领域
        
        Returns:
            面试报告
        """
        session = SessionLocal()
        try:
            # 获取最近5次面试
            records = session.execute(
                text("""
                SELECT score, feedback, transcript
                FROM interviews
                WHERE user_id = :user_id AND domain = :domain
                ORDER BY created_at DESC
                LIMIT 5
                """), {
                    "user_id": user_id,
                    "domain": domain
                }).fetchall()

            if not records:
                return {
                    "avg_score": 0,
                    "weak_points": ["无面试记录"],
                    "progress_tracking": "无面试记录",
                    "real_questions": ["建议先进行面试"]
                }

            avg_score = sum(r[0] for r in records) / len(records)
            low_scores = [r for r in records if r[0] < 3.5]

            # 提取薄弱点
            weak_points = []
            for r in low_scores[:3]:
                if r[1]:
                    # 简单提取反馈中的薄弱点
                    if "劣势" in r[1]:
                        parts = r[1].split("劣势")
                        if len(parts) > 1:
                            weak_points.append(parts[1].split("\n")[0].strip())

            if not weak_points:
                weak_points = ["未识别到明显薄弱点"]

            # 生成学习建议
            recommended_topics = self._recommend_study_topics(weak_points)

            # 生成进度跟踪
            if len(records) > 1:
                if records[0][0] > records[1][0]:
                    progress = f"平均分 {avg_score:.2f}，较上次 ↑"
                else:
                    progress = f"平均分 {avg_score:.2f}，较上次 ↓"
            else:
                progress = f"平均分 {avg_score:.2f}，首次面试"

            return {
                "avg_score": round(avg_score, 2),
                "weak_points": weak_points,
                "progress_tracking": progress,
                "real_questions": recommended_topics
            }
        finally:
            session.close()

    def _generate_report_id(self) -> str:
        """生成报告ID"""
        return f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(datetime.now()) % 10000}"

    def _extract_score(self, feedback: str) -> int:
        """从反馈中提取分数
        
        Args:
            feedback: 面试反馈
        
        Returns:
            提取的分数，如果没有找到则返回0
        """
        # 简单的分数提取逻辑，实际项目中可以使用正则表达式或NLP
        import re
        score_match = re.search(r'面试评分\s*：?\s*(\d+)', feedback)
        if score_match:
            return int(score_match.group(1))
        return 0

    def _extract_conclusion(self, feedback: str) -> str:
        """从反馈中提取结论
        
        Args:
            feedback: 面试反馈
        
        Returns:
            提取的结论
        """
        # 简单的结论提取逻辑，实际项目中可以使用NLP
        lines = feedback.split('\n')
        conclusion = []
        in_conclusion = False

        for line in lines:
            line = line.strip()
            if line.startswith('6. 最终结论') or line.startswith('最终结论'):
                in_conclusion = True
                continue
            if in_conclusion and line and not line.startswith('\d+\.'):
                conclusion.append(line)

        return '\n'.join(conclusion) if conclusion else '未提取到结论'

    def _extract_improvement_suggestions(self, feedback: str) -> List[str]:
        """从反馈中提取改进建议
        
        Args:
            feedback: 面试反馈
        
        Returns:
            改进建议列表
        """
        # 简单的改进建议提取逻辑，实际项目中可以使用NLP
        lines = feedback.split('\n')
        suggestions = []
        in_suggestions = False

        for line in lines:
            line = line.strip()
            if line.startswith('4. 改进建议') or line.startswith('改进建议'):
                in_suggestions = True
                continue
            if in_suggestions and line and not line.startswith('\d+\.'):
                suggestions.append(line)
            elif in_suggestions and line.startswith('\d+\.') and len(
                    suggestions) > 0:
                break

        return suggestions if suggestions else ['未提取到改进建议']

    def generate_technical_report(
            self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成技术面试报告
        
        Args:
            interview_data: 面试数据
        
        Returns:
            技术面试报告
        """
        base_report = self.generate_interview_report(interview_data)

        # 添加技术面试特有内容
        technical_skills = self._analyze_technical_skills(interview_data)
        weak_points = self._identify_weak_points(interview_data)

        base_report.update({
            'report_type':
            'technical',
            'technical_skills':
            technical_skills,
            'weak_points':
            weak_points,
            'recommended_topics':
            self._recommend_study_topics(weak_points)
        })

        return base_report

    def _analyze_technical_skills(
            self, interview_data: Dict[str, Any]) -> Dict[str, int]:
        """分析技术技能掌握情况"""
        # 简单的技术技能分析，实际项目中可以使用NLP
        return {'基础知识': 85, '编程能力': 80, '系统设计': 75, '问题解决': 82, '学习能力': 88}

    def _identify_weak_points(self, interview_data: Dict[str,
                                                         Any]) -> List[str]:
        """识别薄弱点"""
        # 简单的薄弱点识别，实际项目中可以使用NLP
        return ['系统设计能力需要加强', '对某些高级概念理解不够深入', '代码优化能力有待提高']

    def _recommend_study_topics(self, weak_points: List[str]) -> List[str]:
        """推荐学习 topics"""
        # 基于薄弱点推荐学习 topics
        recommendations = []
        for point in weak_points:
            if '系统设计' in point:
                recommendations.append('分布式系统设计')
                recommendations.append('微服务架构')
            if '高级概念' in point:
                recommendations.append('设计模式')
                recommendations.append('算法优化')
            if '代码优化' in point:
                recommendations.append('性能调优')
                recommendations.append('代码重构')
            if '基础' in point:
                recommendations.append('基础知识巩固')
                recommendations.append('核心概念理解')

        return list(set(recommendations))

    def export_report_to_json(self, report: Dict[str, Any], file_path: str):
        """导出报告为JSON格式
        
        Args:
            report: 面试报告
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def export_report_to_markdown(self, report: Dict[str, Any],
                                  file_path: str):
        """导出报告为Markdown格式
        
        Args:
            report: 面试报告
            file_path: 保存路径
        """
        md_content = f"""# 面试报告

## 基本信息
- 报告ID: {report['report_id']}
- 生成时间: {report['generated_at']}
- 面试岗位: {report['interview_role']}
- 面试主题: {report['interview_topic']}
- 面试时长: {report['interview_duration']}分钟
- 问答数量: {report['question_count']}个问题, {report['answer_count']}个回答
- 面试评分: {report['score']}分

## 面试反馈
{report['feedback']}

## 面试历史
"""

        # 添加面试历史
        for i, item in enumerate(report['interview_history']):
            speaker = '面试官' if item['speaker'] == 'interviewer' else '候选人'
            md_content += f"\n### {speaker} ({i+1})\n{item['content']}\n"

        # 添加改进建议
        if report.get('improvement_suggestions'):
            md_content += "\n## 改进建议\n"
            for suggestion in report['improvement_suggestions']:
                md_content += f"- {suggestion}\n"

        # 添加技术报告特有内容
        if report.get('report_type') == 'technical':
            md_content += "\n## 技术技能分析\n"
            for skill, score in report.get('technical_skills', {}).items():
                md_content += f"- {skill}: {score}分\n"

            if report.get('weak_points'):
                md_content += "\n## 薄弱点\n"
                for point in report['weak_points']:
                    md_content += f"- {point}\n"

            if report.get('recommended_topics'):
                md_content += "\n## 推荐学习内容\n"
                for topic in report['recommended_topics']:
                    md_content += f"- {topic}\n"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
