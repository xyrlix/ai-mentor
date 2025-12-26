from typing import List, Dict, Any, Optional, Tuple
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from config import LLM_CONFIG
from .openai_client import create_llm
import json
import re
import os

# 禁用环境变量中的代理设置，防止传递给ChatOpenAI
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)


class ExamOutputParser(BaseOutputParser):
    """考试系统输出解析器"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析考试系统的输出"""
        try:
            # 尝试解析JSON格式
            if text.strip().startswith('{') and text.strip().endswith('}'):
                return json.loads(text.strip())
            
            # 解析试题和答案
            question_match = re.search(r'题目[:：]\s*(.+?)(?=\n答案|\n解析|\n选项|$)', text, re.DOTALL)
            options_match = re.search(r'选项[:：]\s*([\s\S]+?)(?=\n答案|\n解析|$)', text)
            answer_match = re.search(r'答案[:：]\s*(.+)', text)
            explanation_match = re.search(r'解析[:：]\s*(.+)', text, re.DOTALL)
            
            return {
                'question': question_match.group(1).strip() if question_match else text.strip(),
                'options': self.parse_options(options_match.group(1).strip() if options_match else ''),
                'answer': answer_match.group(1).strip() if answer_match else '',
                'explanation': explanation_match.group(1).strip() if explanation_match else '',
                'raw_response': text
            }
        except Exception as e:
            return {
                'question': text.strip(),
                'options': [],
                'answer': '',
                'explanation': '',
                'raw_response': text,
                'error': str(e)
            }
    
    def parse_options(self, options_text: str) -> List[str]:
        """解析选项"""
        if not options_text:
            return []
        
        # 多种格式的选项解析
        options = []
        
        # 格式1: A. 选项内容 B. 选项内容
        option_pattern1 = re.findall(r'([A-D])\.\s*([^A-D]+)', options_text)
        if option_pattern1:
            options = [opt[1].strip() for opt in sorted(option_pattern1, key=lambda x: x[0])]
        
        # 格式2: 1. 选项内容 2. 选项内容
        if not options:
            option_pattern2 = re.findall(r'(\d+)\.\s*([^\d]+)', options_text)
            if option_pattern2:
                options = [opt[1].strip() for opt in sorted(option_pattern2, key=lambda x: int(x[0]))]
        
        # 格式3: - 选项内容
        if not options:
            option_pattern3 = re.findall(r'[-•]\s*([^\n]+)', options_text)
            if option_pattern3:
                options = [opt.strip() for opt in option_pattern3]
        
        return options
    
    @property
    def _type(self) -> str:
        return "exam_output"


class ExamAgent:
    """考试模拟题Agent，支持多种考试类型和题型"""
    
    def __init__(self):
        """初始化考试Agent"""
        self.llm = self.init_llm()
        self.output_parser = ExamOutputParser()
        
        # 考试类型配置
        self.exam_types = {
            'soft_exam': {
                'name': '软件设计师考试',
                'description': '计算机技术与软件专业技术资格（水平）考试',
                'question_types': ['选择题', '简答题', '设计题']
            },
            'pmp': {
                'name': 'PMP项目管理',
                'description': '项目管理专业人士资格认证',
                'question_types': ['选择题', '情景题']
            },
            'cpa': {
                'name': '注册会计师',
                'description': '中国注册会计师考试',
                'question_types': ['选择题', '计算题', '案例分析']
            },
            'teacher': {
                'name': '教师资格证',
                'description': '中小学教师资格考试',
                'question_types': ['选择题', '简答题', '教学设计']
            },
            'law': {
                'name': '法律职业资格',
                'description': '国家统一法律职业资格考试',
                'question_types': ['选择题', '案例分析', '论述题']
            }
        }
        
        # 试题生成提示模板
        self.question_prompt = ChatPromptTemplate.from_template("""
请根据以下要求生成一道{exam_type}的{question_type}试题：

考试主题：{topic}
难度级别：{difficulty}
上下文信息：{context}

请按照以下格式输出：
题目: [试题内容]
选项: [如果是选择题，列出选项A、B、C、D]
答案: [正确答案]
解析: [详细解析]

试题要求：
- 题目清晰明确，无歧义
- 选项设计合理，干扰项有意义
- 答案准确无误
- 解析详细透彻
""")
        
        # 答题评估提示模板
        self.evaluation_prompt = ChatPromptTemplate.from_template("""
请评估以下答题：

题目：{question}
标准答案：{correct_answer}
考生答案：{user_answer}

请从以下维度进行评估：
1. 准确性（0-10分）
2. 完整性（0-10分）
3. 逻辑性（0-10分）
4. 规范性（0-10分）

请给出每个维度的分数和详细评价。
""")
    
    def init_llm(self):
        """初始化大模型"""
        provider = LLM_CONFIG["provider"]
        
        # 检查配置的provider是否有有效的API密钥
        if provider == "qwen" and LLM_CONFIG["qwen_api_key"]:
            return create_llm(
                provider="qwen",
                api_key=LLM_CONFIG["qwen_api_key"],
                api_base=LLM_CONFIG["qwen_api_base"],
                model=LLM_CONFIG["qwen_model"],
                temperature=0.5
            )
        elif provider == "deepseek" and LLM_CONFIG["deepseek_api_key"]:
            return create_llm(
                provider="deepseek",
                api_key=LLM_CONFIG["deepseek_api_key"],
                api_base=LLM_CONFIG["deepseek_api_base"],
                model=LLM_CONFIG["deepseek_model"],
                temperature=0.5
            )
        elif provider == "zhipu" and LLM_CONFIG["zhipu_api_key"]:
            return create_llm(
                provider="zhipu",
                api_key=LLM_CONFIG["zhipu_api_key"],
                api_base=LLM_CONFIG["zhipu_api_base"],
                model=LLM_CONFIG["zhipu_model"],
                temperature=0.5
            )
        elif provider == "openai" and LLM_CONFIG["openai_api_key"]:
            return create_llm(
                provider="openai",
                api_key=LLM_CONFIG["openai_api_key"],
                api_base=LLM_CONFIG["openai_api_base"],
                model=LLM_CONFIG["openai_model"],
                temperature=0.5
            )
        
        # 如果配置的provider没有有效密钥，尝试其他可用的provider
        print(f"警告: {provider} API密钥未配置，尝试使用其他可用模型")
        
        # 按优先级尝试其他模型
        if LLM_CONFIG["qwen_api_key"]:
            print("使用通义千问模型作为备选")
            return create_llm(
                provider="qwen",
                api_key=LLM_CONFIG["qwen_api_key"],
                api_base=LLM_CONFIG["qwen_api_base"],
                model=LLM_CONFIG["qwen_model"],
                temperature=0.5
            )
        elif LLM_CONFIG["deepseek_api_key"]:
            print("使用深度求索模型作为备选")
            return create_llm(
                provider="deepseek",
                api_key=LLM_CONFIG["deepseek_api_key"],
                api_base=LLM_CONFIG["deepseek_api_base"],
                model=LLM_CONFIG["deepseek_model"],
                temperature=0.5
            )
        elif LLM_CONFIG["zhipu_api_key"]:
            print("使用智谱AI模型作为备选")
            return create_llm(
                provider="zhipu",
                api_key=LLM_CONFIG["zhipu_api_key"],
                api_base=LLM_CONFIG["zhipu_api_base"],
                model=LLM_CONFIG["zhipu_model"],
                temperature=0.5
            )
        elif LLM_CONFIG["openai_api_key"]:
            print("使用OpenAI模型作为备选")
            return create_llm(
                provider="openai",
                api_key=LLM_CONFIG["openai_api_key"],
                api_base=LLM_CONFIG["openai_api_base"],
                model=LLM_CONFIG["openai_model"],
                temperature=0.5
            )
        
        # 如果所有模型都不可用，返回一个模拟的LLM实例，让应用能够启动但禁用相关功能
        print("警告: 所有大模型API密钥均未配置，考试功能将被禁用，但应用可以正常启动")
        
        # 创建一个模拟的ChatOpenAI实例，避免应用崩溃
        class MockLLM:
            def __init__(self):
                self.temperature = 0.5
                
            def invoke(self, *args, **kwargs):
                return {
                    'content': '由于未配置有效的大模型API密钥，AI功能暂时不可用。请配置有效的API密钥后重试。',
                    'status': 'mock_response'
                }
        
        return MockLLM()
    
    def get_exam_types(self) -> Dict[str, Dict]:
        """获取支持的考试类型"""
        return self.exam_types
    
    def generate_question(self, exam_type: str, question_type: str, 
                         topic: str, difficulty: str = "中等", 
                         context: str = "") -> Dict[str, Any]:
        """生成考试试题
        
        Args:
            exam_type: 考试类型
            question_type: 题型
            topic: 主题
            difficulty: 难度
            context: 上下文信息
        
        Returns:
            试题信息
        """
        try:
            # 验证考试类型和题型
            if exam_type not in self.exam_types:
                raise ValueError(f"不支持的考试类型: {exam_type}")
            
            if question_type not in self.exam_types[exam_type]['question_types']:
                raise ValueError(f"不支持的题型: {question_type}")
            
            chain = self.question_prompt | self.llm | self.output_parser
            result = chain.invoke({
                "exam_type": self.exam_types[exam_type]['name'],
                "question_type": question_type,
                "topic": topic,
                "difficulty": difficulty,
                "context": context
            })
            
            # 添加试题元数据
            result.update({
                'exam_type': exam_type,
                'question_type': question_type,
                'difficulty': difficulty,
                'topic': topic,
                'generated_at': self.get_current_time()
            })
            
            return result
            
        except Exception as e:
            return {
                'error': f"生成试题失败: {str(e)}",
                'exam_type': exam_type,
                'question_type': question_type,
                'difficulty': difficulty,
                'topic': topic
            }
    
    def generate_question_set(self, exam_type: str, topic: str, 
                            count: int = 10, difficulty: str = "中等",
                            context: str = "") -> List[Dict[str, Any]]:
        """生成试题集
        
        Args:
            exam_type: 考试类型
            topic: 主题
            count: 试题数量
            difficulty: 难度
            context: 上下文信息
        
        Returns:
            试题集
        """
        questions = []
        question_types = self.exam_types[exam_type]['question_types']
        
        for i in range(count):
            # 轮换题型
            question_type = question_types[i % len(question_types)]
            
            question = self.generate_question(
                exam_type=exam_type,
                question_type=question_type,
                topic=topic,
                difficulty=difficulty,
                context=context
            )
            
            if 'error' not in question:
                question['id'] = i + 1
                questions.append(question)
            
            # 避免过快请求
            import time
            time.sleep(0.5)
        
        return questions
    
    def evaluate_answer(self, question: str, correct_answer: str, 
                       user_answer: str) -> Dict[str, Any]:
        """评估答题
        
        Args:
            question: 题目
            correct_answer: 标准答案
            user_answer: 考生答案
        
        Returns:
            评估结果
        """
        try:
            chain = self.evaluation_prompt | self.llm
            response = chain.invoke({
                "question": question,
                "correct_answer": correct_answer,
                "user_answer": user_answer
            })
            
            content = response.content.strip()
            
            # 解析评分
            scores = re.findall(r'(\d+)\s*分', content)
            
            return {
                'evaluation': content,
                'accuracy': int(scores[0]) if len(scores) > 0 else 5,
                'completeness': int(scores[1]) if len(scores) > 1 else 5,
                'logic': int(scores[2]) if len(scores) > 2 else 5,
                'standardization': int(scores[3]) if len(scores) > 3 else 5,
                'overall_score': sum([int(scores[i]) for i in range(min(4, len(scores)))]) / min(4, len(scores))
            }
            
        except Exception as e:
            return {
                'evaluation': f"评估失败: {str(e)}",
                'accuracy': 5,
                'completeness': 5,
                'logic': 5,
                'standardization': 5,
                'overall_score': 5,
                'error': str(e)
            }
    
    def simulate_exam(self, exam_type: str, topic: str, 
                     question_count: int = 20, time_limit: int = 120) -> Dict[str, Any]:
        """模拟考试
        
        Args:
            exam_type: 考试类型
            topic: 主题
            question_count: 题目数量
            time_limit: 时间限制（分钟）
        
        Returns:
            模拟考试结果
        """
        try:
            # 生成试题集
            questions = self.generate_question_set(
                exam_type=exam_type,
                topic=topic,
                count=question_count,
                context=""
            )
            
            exam_info = {
                'exam_type': exam_type,
                'exam_name': self.exam_types[exam_type]['name'],
                'topic': topic,
                'question_count': len(questions),
                'time_limit': time_limit,
                'questions': questions,
                'created_at': self.get_current_time()
            }
            
            return exam_info
            
        except Exception as e:
            return {
                'error': f"模拟考试生成失败: {str(e)}",
                'exam_type': exam_type,
                'topic': topic
            }
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def calculate_score(self, answers: Dict[int, str], 
                       questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算考试成绩
        
        Args:
            answers: 考生答案 {题号: 答案}
            questions: 试题列表
        
        Returns:
            成绩报告
        """
        try:
            correct_count = 0
            total_score = 0
            detailed_results = []
            
            for i, question in enumerate(questions):
                question_id = question.get('id', i + 1)
                user_answer = answers.get(question_id, '')
                correct_answer = question.get('answer', '')
                
                # 简单匹配评估
                is_correct = self.is_answer_correct(user_answer, correct_answer)
                score = 10 if is_correct else 0
                
                detailed_results.append({
                    'question_id': question_id,
                    'question': question.get('question', ''),
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'score': score,
                    'explanation': question.get('explanation', '')
                })
                
                if is_correct:
                    correct_count += 1
                    total_score += score
            
            # 计算百分比
            accuracy = (correct_count / len(questions)) * 100 if questions else 0
            
            return {
                'total_questions': len(questions),
                'correct_count': correct_count,
                'accuracy': round(accuracy, 2),
                'total_score': total_score,
                'max_score': len(questions) * 10,
                'detailed_results': detailed_results,
                'grade': self.get_grade(accuracy)
            }
            
        except Exception as e:
            return {
                'error': f"成绩计算失败: {str(e)}",
                'total_questions': len(questions),
                'correct_count': 0,
                'accuracy': 0,
                'total_score': 0,
                'max_score': len(questions) * 10
            }
    
    def is_answer_correct(self, user_answer: str, correct_answer: str) -> bool:
        """判断答案是否正确（简单实现）"""
        # 去除空格和大小写差异
        user_clean = user_answer.strip().lower()
        correct_clean = correct_answer.strip().lower()
        
        # 直接匹配
        if user_clean == correct_clean:
            return True
        
        # 选择题选项匹配（A vs A. 内容）
        if len(user_clean) == 1 and len(correct_clean) > 1:
            if correct_clean.startswith(user_clean):
                return True
        
        # 相似度匹配（简单实现）
        if self.similarity(user_clean, correct_clean) > 0.8:
            return True
        
        return False
    
    def similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度（简单实现）"""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard相似度
        set1 = set(str1)
        set2 = set(str2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_grade(self, accuracy: float) -> str:
        """根据准确率获取等级"""
        if accuracy >= 90:
            return "优秀"
        elif accuracy >= 80:
            return "良好"
        elif accuracy >= 70:
            return "中等"
        elif accuracy >= 60:
            return "及格"
        else:
            return "不及格"


# 全局考试Agent实例
exam_agent = None


def get_exam_agent():
    """获取考试Agent实例"""
    global exam_agent
    if exam_agent is None:
        exam_agent = ExamAgent()
    return exam_agent