from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from .prompt_templates import interview_prompts, get_prompt_template
from config import LLM_CONFIG
import os

# 禁用环境变量中的代理设置，防止传递给ChatOpenAI
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)


class InterviewerAgent:
    """多场景面试Agent，支持不同岗位类型的面试"""

    def __init__(self):
        """初始化面试Agent"""
        self.llm = self.init_llm()
        self.memory = ConversationBufferMemory()
        self.conversation = ConversationChain(llm=self.llm, memory=self.memory)
        self.current_role = None
        self.current_topic = None
        self.interview_history = []

    def init_llm(self):
        """初始化大模型，支持多个国产模型提供商"""
        provider = LLM_CONFIG["provider"]

        # 检查配置的provider是否有有效的API密钥
        if provider == "qwen" and LLM_CONFIG["qwen_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["qwen_api_key"],
                              openai_api_base=LLM_CONFIG["qwen_api_base"],
                              model=LLM_CONFIG["qwen_model"],
                              temperature=LLM_CONFIG["temperature"])
        elif provider == "deepseek" and LLM_CONFIG["deepseek_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["deepseek_api_key"],
                              openai_api_base=LLM_CONFIG["deepseek_api_base"],
                              model=LLM_CONFIG["deepseek_model"],
                              temperature=LLM_CONFIG["temperature"])
        elif provider == "zhipu" and LLM_CONFIG["zhipu_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["zhipu_api_key"],
                              openai_api_base=LLM_CONFIG["zhipu_api_base"],
                              model=LLM_CONFIG["zhipu_model"],
                              temperature=LLM_CONFIG["temperature"])
        elif provider == "openai" and LLM_CONFIG["openai_api_key"]:
            return ChatOpenAI(openai_api_key=LLM_CONFIG["openai_api_key"],
                              openai_api_base=LLM_CONFIG["openai_api_base"],
                              model=LLM_CONFIG["openai_model"],
                              temperature=LLM_CONFIG["temperature"])
        
        # 如果配置的provider没有有效密钥，尝试其他可用的provider
        print(f"警告: {provider} API密钥未配置，尝试使用其他可用模型")
        
        # 按优先级尝试其他模型
        if LLM_CONFIG["qwen_api_key"]:
            print("使用通义千问模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["qwen_api_key"],
                              openai_api_base=LLM_CONFIG["qwen_api_base"],
                              model=LLM_CONFIG["qwen_model"],
                              temperature=LLM_CONFIG["temperature"])
        elif LLM_CONFIG["deepseek_api_key"]:
            print("使用深度求索模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["deepseek_api_key"],
                              openai_api_base=LLM_CONFIG["deepseek_api_base"],
                              model=LLM_CONFIG["deepseek_model"],
                              temperature=LLM_CONFIG["temperature"])
        elif LLM_CONFIG["zhipu_api_key"]:
            print("使用智谱AI模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["zhipu_api_key"],
                              openai_api_base=LLM_CONFIG["zhipu_api_base"],
                              model=LLM_CONFIG["zhipu_model"],
                              temperature=LLM_CONFIG["temperature"])
        elif LLM_CONFIG["openai_api_key"]:
            print("使用OpenAI模型作为备选")
            return ChatOpenAI(openai_api_key=LLM_CONFIG["openai_api_key"],
                              openai_api_base=LLM_CONFIG["openai_api_base"],
                              model=LLM_CONFIG["openai_model"],
                              temperature=LLM_CONFIG["temperature"])
        
        # 如果所有模型都不可用，返回一个模拟的LLM实例，让应用能够启动但禁用相关功能
        print("警告: 所有大模型API密钥均未配置，面试功能将被禁用，但应用可以正常启动")
        
        # 创建一个模拟的ChatOpenAI实例，避免应用崩溃
        class MockLLM:
            def __init__(self):
                self.temperature = LLM_CONFIG["temperature"]
                
            def predict(self, input: str):
                return "由于未配置有效的大模型API密钥，AI功能暂时不可用。请配置有效的API密钥后重试。"
        
        return MockLLM()

    def set_role(self, role: str):
        """设置面试角色（岗位类型）"""
        self.current_role = role
        if role in interview_prompts:
            # 初始化对话历史，使用对应角色的提示模板
            self.memory.clear()
            self.conversation.prompt.template = interview_prompts[role]
        else:
            raise ValueError(f"不支持的角色: {role}")

    def start_interview(self, topic: str = None) -> str:
        """开始面试
        
        Args:
            topic: 面试主题
        
        Returns:
            面试官的开场白
        """
        self.current_topic = topic
        initial_prompt = f"请开始一场关于{topic}的面试。首先做个自我介绍，然后提出第一个问题。"
        response = self.conversation.predict(input=initial_prompt)
        self.interview_history.append({
            'speaker': 'interviewer',
            'content': response
        })
        return response

    def ask_question(self, user_answer: str) -> str:
        """根据用户回答生成下一个问题
        
        Args:
            user_answer: 用户的回答
        
        Returns:
            面试官的下一个问题
        """
        self.interview_history.append({
            'speaker': 'candidate',
            'content': user_answer
        })

        # 生成下一个问题的提示
        prompt = f"基于候选人的回答，提出一个相关的、深入的后续问题，保持面试的流畅性。"
        response = self.conversation.predict(input=prompt)

        self.interview_history.append({
            'speaker': 'interviewer',
            'content': response
        })
        return response

    def run_interview(self, scene_type: str, user_answer: str,
                      last_question: str, context: str,
                      history: str) -> Dict[str, Any]:
        """运行面试流程，根据场景类型和用户回答生成反馈
        
        Args:
            scene_type: 场景类型
            user_answer: 用户回答
            last_question: 上一个问题
            context: 上下文
            history: 历史对话
        
        Returns:
            包含评分、后续问题和评论的反馈
        """
        # 获取场景对应的提示模板
        prompt = get_prompt_template(scene_type)

        # 构建对话链
        chain = prompt | self.llm

        # 调用大模型
        response = chain.invoke({
            "history": history,
            "context": context,
            "question": last_question,
            "user_answer": user_answer
        })

        # 解析输出：score follow_up comment
        content = response.content.strip()
        parts = content.split("\n")

        # 简单解析，实际项目中可能需要更复杂的解析逻辑
        return {
            "score": float(parts[0].strip() if parts else "0"),
            "follow_up": parts[1].strip() if len(parts) > 1 else "",
            "comment": parts[2].strip() if len(parts) > 2 else ""
        }

    def evaluate_answer(self, user_answer: str,
                        question: str) -> Dict[str, Any]:
        """评估用户回答
        
        Args:
            user_answer: 用户的回答
            question: 对应的问题
        
        Returns:
            评估结果，包含分数、优缺点等
        """
        eval_prompt = f"""
        请评估候选人对以下问题的回答：
        问题：{question}
        回答：{user_answer}
        
        评估维度：
        1. 准确性（0-10分）
        2. 深度和完整性（0-10分）
        3. 逻辑性（0-10分）
        4. 实用性（0-10分）
        5. 创新性（0-10分）
        
        请给出每个维度的分数，并提供总体评价和改进建议。
        """

        response = self.conversation.predict(input=eval_prompt)
        return {
            'user_answer': user_answer,
            'question': question,
            'evaluation': response
        }

    def end_interview(self) -> str:
        """结束面试
        
        Returns:
            面试官的结束语
        """
        end_prompt = "请结束这场面试，做一个简短的总结，并感谢候选人。"
        response = self.conversation.predict(input=end_prompt)
        self.interview_history.append({
            'speaker': 'interviewer',
            'content': response
        })
        return response

    def get_interview_history(self) -> List[Dict]:
        """获取面试历史记录"""
        return self.interview_history

    def generate_feedback(self) -> Dict[str, Any]:
        """生成面试反馈
        
        Returns:
            详细的面试反馈报告
        """
        feedback_prompt = f"""
        基于以下面试历史，生成一份详细的面试反馈报告：
        {self.interview_history}
        
        报告应包含：
        1. 总体评价
        2. 候选人优势
        3. 候选人劣势
        4. 改进建议
        5. 面试评分（0-100分）
        6. 最终结论
        """

        response = self.conversation.predict(input=feedback_prompt)
        return {
            'feedback': response,
            'interview_history': self.interview_history,
            'role': self.current_role,
            'topic': self.current_topic
        }
