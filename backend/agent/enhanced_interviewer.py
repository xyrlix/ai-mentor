from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from config import LLM_CONFIG
import json
import re
import os

# 禁用环境变量中的代理设置，防止传递给ChatOpenAI
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)


class EnhancedInterviewerOutputParser(BaseOutputParser):
    """增强面试官输出解析器"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析面试官输出"""
        try:
            # 尝试解析JSON格式
            if text.strip().startswith('{') and text.strip().endswith('}'):
                return json.loads(text.strip())
            
            # 解析结构化输出
            score_match = re.search(r'评分[:：]\s*(\d+)', text)
            question_match = re.search(r'问题[:：]\s*(.+)', text, re.DOTALL)
            feedback_match = re.search(r'反馈[:：]\s*(.+)', text, re.DOTALL)
            
            return {
                'score': int(score_match.group(1)) if score_match else 7,
                'question': question_match.group(1).strip() if question_match else text.strip(),
                'feedback': feedback_match.group(1).strip() if feedback_match else '无详细反馈',
                'raw_response': text
            }
        except Exception as e:
            return {
                'score': 7,
                'question': text.strip(),
                'feedback': '解析失败',
                'raw_response': text,
                'error': str(e)
            }
    
    @property
    def _type(self) -> str:
        return "enhanced_interviewer_output"


class EnhancedInterviewerAgent:
    """增强版AI面试官，支持更多角色和场景"""
    
    def __init__(self):
        """初始化增强面试官"""
        self.llm = self.init_llm()
        self.output_parser = EnhancedInterviewerOutputParser()
        
        # 面试角色配置
        self.interview_roles = {
            'technical_lead': {
                'name': '技术主管',
                'description': '负责技术团队管理和技术决策',
                'focus_areas': ['技术架构', '团队管理', '技术决策']
            },
            'hr_manager': {
                'name': 'HR经理',
                'description': '负责人才招聘和人力资源管理',
                'focus_areas': ['沟通能力', '团队合作', '职业规划']
            },
            'product_director': {
                'name': '产品总监',
                'description': '负责产品战略和产品管理',
                'focus_areas': ['产品思维', '市场分析', '用户体验']
            },
            'cto': {
                'name': 'CTO',
                'description': '首席技术官，负责技术战略',
                'focus_areas': ['技术战略', '创新思维', '商业洞察']
            },
            'language_expert': {
                'name': '语言专家',
                'description': '负责语言能力评估',
                'focus_areas': ['语言流利度', '表达能力', '文化理解']
            }
        }
        
        # 面试场景配置
        self.interview_scenarios = {
            'behavioral': '行为面试',
            'technical': '技术面试', 
            'case_study': '案例分析',
            'system_design': '系统设计',
            'stress_test': '压力测试',
            'cultural_fit': '文化匹配'
        }
        
        # 面试提示模板
        self.interview_prompt = ChatPromptTemplate.from_template("""
你是一位经验丰富的{role_name}，正在进行一场{scenario_name}面试。

候选人背景：{candidate_background}
面试职位：{position}

面试要求：
1. 根据候选人的回答提出深入的问题
2. 评估候选人的专业能力和软技能
3. 关注候选人的思考过程和解决问题的能力
4. 保持面试的专业性和流畅性

请根据以下信息生成面试反馈：
候选人回答：{user_answer}

输出格式：
评分: [1-10分]
问题: [下一个问题]
反馈: [详细反馈]
""")
    
    def init_llm(self):
        """初始化大模型"""
        provider = LLM_CONFIG["provider"]
        
        # 检查配置的provider是否有有效的API密钥
        if provider == "qwen" and LLM_CONFIG["qwen_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["qwen_api_key"],
                            openai_api_base=LLM_CONFIG["qwen_api_base"],
                            model=LLM_CONFIG["qwen_model"],
                            temperature=0.7)
        elif provider == "deepseek" and LLM_CONFIG["deepseek_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["deepseek_api_key"],
                            openai_api_base=LLM_CONFIG["deepseek_api_base"],
                            model=LLM_CONFIG["deepseek_model"],
                            temperature=0.7)
        elif provider == "zhipu" and LLM_CONFIG["zhipu_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["zhipu_api_key"],
                            openai_api_base=LLM_CONFIG["zhipu_api_base"],
                            model=LLM_CONFIG["zhipu_model"],
                            temperature=0.7)
        elif provider == "openai" and LLM_CONFIG["openai_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["openai_api_key"],
                            openai_api_base=LLM_CONFIG["openai_api_base"],
                            model=LLM_CONFIG["openai_model"],
                            temperature=0.7)
        
        # 如果配置的provider没有有效密钥，尝试其他可用的provider
        print(f"警告: {provider} API密钥未配置，尝试使用其他可用模型")
        
        # 按优先级尝试其他模型
        if LLM_CONFIG["qwen_api_key"]:
            print("使用通义千问模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["qwen_api_key"],
                            openai_api_base=LLM_CONFIG["qwen_api_base"],
                            model=LLM_CONFIG["qwen_model"],
                            temperature=0.7)
        elif LLM_CONFIG["deepseek_api_key"]:
            print("使用深度求索模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["deepseek_api_key"],
                            openai_api_base=LLM_CONFIG["deepseek_api_base"],
                            model=LLM_CONFIG["deepseek_model"],
                            temperature=0.7)
        elif LLM_CONFIG["zhipu_api_key"]:
            print("使用智谱AI模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["zhipu_api_key"],
                            openai_api_base=LLM_CONFIG["zhipu_api_base"],
                            model=LLM_CONFIG["zhipu_model"],
                            temperature=0.7)
        elif LLM_CONFIG["openai_api_key"]:
            print("使用OpenAI模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["openai_api_key"],
                            openai_api_base=LLM_CONFIG["openai_api_base"],
                            model=LLM_CONFIG["openai_model"],
                            temperature=0.7)
        
        # 如果所有模型都不可用，返回一个模拟的LLM实例，让应用能够启动但禁用相关功能
        print("警告: 所有大模型API密钥均未配置，增强面试功能将被禁用，但应用可以正常启动")
        
        # 创建一个模拟的ChatOpenAI实例，避免应用崩溃
        class MockLLM:
            def __init__(self):
                self.temperature = 0.7
                
            def invoke(self, *args, **kwargs):
                return {
                    'content': '由于未配置有效的大模型API密钥，AI功能暂时不可用。请配置有效的API密钥后重试。',
                    'status': 'mock_response'
                }
        
        return MockLLM()
    
    def get_available_roles(self) -> Dict[str, Dict]:
        """获取可用的面试角色"""
        return self.interview_roles
    
    def get_available_scenarios(self) -> Dict[str, str]:
        """获取可用的面试场景"""
        return self.interview_scenarios
    
    def conduct_interview(self, role: str, scenario: str, 
                         user_answer: str, candidate_background: str = "",
                         position: str = "软件工程师") -> Dict[str, Any]:
        """进行面试
        
        Args:
            role: 面试官角色
            scenario: 面试场景
            user_answer: 用户回答
            candidate_background: 候选人背景
            position: 面试职位
        
        Returns:
            面试结果
        """
        try:
            # 验证角色和场景
            if role not in self.interview_roles:
                raise ValueError(f"不支持的面试角色: {role}")
            
            if scenario not in self.interview_scenarios:
                raise ValueError(f"不支持的面试场景: {scenario}")
            
            role_name = self.interview_roles[role]['name']
            scenario_name = self.interview_scenarios[scenario]
            
            chain = self.interview_prompt | self.llm | self.output_parser
            result = chain.invoke({
                "role_name": role_name,
                "scenario_name": scenario_name,
                "candidate_background": candidate_background,
                "position": position,
                "user_answer": user_answer
            })
            
            # 添加元数据
            result.update({
                'role': role,
                'scenario': scenario,
                'role_name': role_name,
                'scenario_name': scenario_name,
                'timestamp': self.get_current_time()
            })
            
            return result
            
        except Exception as e:
            return {
                'error': f"面试处理失败: {str(e)}",
                'role': role,
                'scenario': scenario,
                'score': 0,
                'question': '面试出现错误，请重试。',
                'feedback': str(e)
            }
    
    def evaluate_candidate_profile(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估候选人整体档案
        
        Args:
            candidate_data: 候选人数据
        
        Returns:
            评估结果
        """
        try:
            evaluation_prompt = """
请基于以下候选人信息进行综合评估：

候选人信息：
{profile}

请从以下维度进行评估（1-10分）：
1. 技术能力
2. 沟通能力
3. 问题解决能力
4. 团队合作能力
5. 学习能力
6. 领导潜力

请给出每个维度的评分和总体建议。
"""
            
            prompt = ChatPromptTemplate.from_template(evaluation_prompt)
            chain = prompt | self.llm
            response = chain.invoke({
                "profile": json.dumps(candidate_data, ensure_ascii=False, indent=2)
            })
            
            content = response.content.strip()
            
            # 解析评分
            scores = re.findall(r'(\d+)\s*分', content)
            
            return {
                'evaluation': content,
                'technical_skill': int(scores[0]) if len(scores) > 0 else 5,
                'communication': int(scores[1]) if len(scores) > 1 else 5,
                'problem_solving': int(scores[2]) if len(scores) > 2 else 5,
                'teamwork': int(scores[3]) if len(scores) > 3 else 5,
                'learning_ability': int(scores[4]) if len(scores) > 4 else 5,
                'leadership': int(scores[5]) if len(scores) > 5 else 5,
                'overall_score': sum([int(scores[i]) for i in range(min(6, len(scores)))]) / min(6, len(scores))
            }
            
        except Exception as e:
            return {
                'evaluation': f"评估失败: {str(e)}",
                'technical_skill': 5,
                'communication': 5,
                'problem_solving': 5,
                'teamwork': 5,
                'learning_ability': 5,
                'leadership': 5,
                'overall_score': 5,
                'error': str(e)
            }
    
    def generate_interview_questions(self, role: str, scenario: str, 
                                   topic: str, difficulty: str = "中等") -> List[str]:
        """生成面试问题列表
        
        Args:
            role: 面试官角色
            scenario: 面试场景
            topic: 主题
            difficulty: 难度
        
        Returns:
            问题列表
        """
        try:
            questions_prompt = """
作为{role_name}，请为{scenario_name}面试生成5个关于{topic}的问题。
难度级别：{difficulty}

请生成专业、深入的问题，涵盖不同层次的知识点。
"""
            
            role_name = self.interview_roles[role]['name']
            scenario_name = self.interview_scenarios[scenario]
            
            prompt = ChatPromptTemplate.from_template(questions_prompt)
            chain = prompt | self.llm
            response = chain.invoke({
                "role_name": role_name,
                "scenario_name": scenario_name,
                "topic": topic,
                "difficulty": difficulty
            })
            
            # 解析生成的问题
            content = response.content.strip()
            questions = re.findall(r'\d+\.\s*(.+?)(?=\n|$)', content)
            
            return questions if questions else [
                f"请介绍一下你对{topic}的理解",
                f"在{topic}方面，你最大的挑战是什么？",
                f"如何将{topic}应用到实际项目中？",
                f"谈谈{topic}的最新发展趋势",
                f"你在{topic}方面的职业规划是什么？"
            ]
            
        except Exception as e:
            return [
                f"请介绍一下你对{topic}的理解",
                f"在{topic}方面，你最大的挑战是什么？",
                f"如何将{topic}应用到实际项目中？",
                f"谈谈{topic}的最新发展趋势",
                f"你在{topic}方面的职业规划是什么？"
            ]
    
    def provide_career_advice(self, candidate_data: Dict[str, Any], 
                            target_role: str) -> Dict[str, Any]:
        """提供职业发展建议
        
        Args:
            candidate_data: 候选人数据
            target_role: 目标职位
        
        Returns:
            职业建议
        """
        try:
            advice_prompt = """
基于以下候选人信息和目标职位，提供职业发展建议：

候选人信息：
{profile}

目标职位：{target_role}

请提供：
1. 当前能力与目标职位的差距分析
2. 具体的学习和发展建议
3. 短期和长期的职业规划
4. 推荐的技能提升路径
"""
            
            prompt = ChatPromptTemplate.from_template(advice_prompt)
            chain = prompt | self.llm
            response = chain.invoke({
                "profile": json.dumps(candidate_data, ensure_ascii=False, indent=2),
                "target_role": target_role
            })
            
            return {
                'career_advice': response.content.strip(),
                'target_role': target_role,
                'generated_at': self.get_current_time()
            }
            
        except Exception as e:
            return {
                'career_advice': f"生成职业建议失败: {str(e)}",
                'target_role': target_role,
                'error': str(e)
            }
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 全局增强面试官实例
enhanced_interviewer = None


def get_enhanced_interviewer():
    """获取增强面试官实例"""
    global enhanced_interviewer
    if enhanced_interviewer is None:
        enhanced_interviewer = EnhancedInterviewerAgent()
    return enhanced_interviewer