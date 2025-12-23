from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from config import LLM_CONFIG
import json
import re
import os

# 彻底禁用所有可能的代理环境变量
proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']
for var in proxy_env_vars:
    os.environ.pop(var, None)

# 导入openai库直接创建客户端，并手动创建httpx客户端
import openai
import httpx


class QnAOutputParser(BaseOutputParser):
    """问答系统输出解析器"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析问答系统的输出"""
        try:
            # 尝试解析JSON格式
            if text.strip().startswith('{') and text.strip().endswith('}'):
                return json.loads(text.strip())
            
            # 否则使用正则表达式解析
            answer_match = re.search(r'答案[:：]\s*(.+)', text, re.DOTALL)
            confidence_match = re.search(r'置信度[:：]\s*(\d+\.?\d*)', text)
            sources_match = re.search(r'来源[:：]\s*(.+)', text)
            
            return {
                'answer': answer_match.group(1).strip() if answer_match else text.strip(),
                'confidence': float(confidence_match.group(1)) if confidence_match else 0.8,
                'sources': sources_match.group(1).strip().split('，') if sources_match else [],
                'raw_response': text
            }
        except Exception as e:
            return {
                'answer': text.strip(),
                'confidence': 0.5,
                'sources': [],
                'raw_response': text,
                'error': str(e)
            }
    
    @property
    def _type(self) -> str:
        return "qna_output"


class QnAAgent:
    """智能问答Agent，支持基于知识库的问答"""
    
    def __init__(self):
        """初始化问答Agent"""
        self.llm = self.init_llm()
        self.output_parser = QnAOutputParser()
        
        # 问答提示模板
        self.qna_prompt = ChatPromptTemplate.from_template("""
你是一个专业的AI知识问答助手。请基于以下上下文信息，准确、清晰地回答用户的问题。

上下文信息：
{context}

用户问题：{question}

历史对话：
{history}

请按照以下格式输出：
答案: [你的回答]
置信度: [0-1之间的数字，表示答案的可靠程度]
来源: [相关来源，用中文逗号分隔]

如果无法从上下文中找到答案，请明确说明并建议用户提供更多信息。
""")
        
        # 多轮对话提示模板
        self.conversation_prompt = ChatPromptTemplate.from_template("""
你正在与用户进行多轮对话。以下是对话历史：

{history}

当前用户的问题：{question}

上下文信息：{context}

请根据对话历史和当前问题，给出连贯、有帮助的回答。
""")
    
    def init_llm(self):
        """初始化大模型"""
        provider = LLM_CONFIG["provider"]
        
        # 检查配置的provider是否有有效的API密钥
        if provider == "qwen" and LLM_CONFIG["qwen_api_key"]:
            try:
                return ChatOpenAI(
                    openai_api_key=LLM_CONFIG["qwen_api_key"],
                    openai_api_base=LLM_CONFIG["qwen_api_base"],
                    model=LLM_CONFIG["qwen_model"],
                    temperature=0.3
                )
            except Exception as e:
                print(f"ChatOpenAI初始化失败，使用模拟LLM: {e}")
        elif provider == "deepseek" and LLM_CONFIG["deepseek_api_key"]:
            try:
                return ChatOpenAI(
                    openai_api_key=LLM_CONFIG["deepseek_api_key"],
                    openai_api_base=LLM_CONFIG["deepseek_api_base"],
                    model=LLM_CONFIG["deepseek_model"],
                    temperature=0.3
                )
            except Exception as e:
                print(f"ChatOpenAI初始化失败，使用模拟LLM: {e}")
        elif provider == "zhipu" and LLM_CONFIG["zhipu_api_key"]:
            try:
                return ChatOpenAI(
                    openai_api_key=LLM_CONFIG["zhipu_api_key"],
                    openai_api_base=LLM_CONFIG["zhipu_api_base"],
                    model=LLM_CONFIG["zhipu_model"],
                    temperature=0.3
                )
            except Exception as e:
                print(f"ChatOpenAI初始化失败，使用模拟LLM: {e}")
        elif provider == "openai" and LLM_CONFIG["openai_api_key"]:
            try:
                return ChatOpenAI(
                    openai_api_key=LLM_CONFIG["openai_api_key"],
                    openai_api_base=LLM_CONFIG["openai_api_base"],
                    model=LLM_CONFIG["openai_model"],
                    temperature=0.3
                )
            except Exception as e:
                print(f"ChatOpenAI初始化失败，使用模拟LLM: {e}")
        
        # 如果配置的provider没有有效密钥，尝试其他可用的provider
        print(f"警告: {provider} API密钥未配置或初始化失败，尝试使用其他可用模型")
        
        # 按优先级尝试其他模型
        for provider_name, api_key, api_base, model_name in [
            ("qwen", LLM_CONFIG["qwen_api_key"], LLM_CONFIG["qwen_api_base"], LLM_CONFIG["qwen_model"]),
            ("deepseek", LLM_CONFIG["deepseek_api_key"], LLM_CONFIG["deepseek_api_base"], LLM_CONFIG["deepseek_model"]),
            ("zhipu", LLM_CONFIG["zhipu_api_key"], LLM_CONFIG["zhipu_api_base"], LLM_CONFIG["zhipu_model"]),
            ("openai", LLM_CONFIG["openai_api_key"], LLM_CONFIG["openai_api_base"], LLM_CONFIG["openai_model"])
        ]:
            if api_key:
                try:
                    print(f"尝试使用{provider_name}模型")
                    return ChatOpenAI(
                        openai_api_key=api_key,
                        openai_api_base=api_base,
                        model=model_name,
                        temperature=0.3
                    )
                except Exception as e:
                    print(f"{provider_name}模型初始化失败: {e}")
                    continue
        
        # 如果所有模型都不可用，返回一个模拟的LLM实例，让应用能够启动但禁用相关功能
        print("警告: 所有大模型API密钥均未配置或初始化失败，问答功能将被禁用，但应用可以正常启动")
        
        # 创建一个模拟的LLM实例，避免应用崩溃
        class MockLLM:
            def __init__(self):
                self.temperature = 0.3
                
            def invoke(self, *args, **kwargs):
                # 创建一个模拟LangChain响应对象
                class MockResponse:
                    def __init__(self, content):
                        self.content = content
                
                return MockResponse('由于未配置有效的大模型API密钥，AI功能暂时不可用。请配置有效的API密钥后重试。')
        
        return MockLLM()
    
    def answer_question(self, question: str, context: str, 
                       history: str = "", conversation_mode: bool = False) -> Dict[str, Any]:
        """回答问题
        
        Args:
            question: 用户问题
            context: 上下文信息（来自知识库检索）
            history: 历史对话
            conversation_mode: 是否为多轮对话模式
        
        Returns:
            回答结果
        """
        try:
            if conversation_mode and history:
                prompt = self.conversation_prompt
                chain = prompt | self.llm
                response = chain.invoke({
                    "question": question,
                    "context": context,
                    "history": history
                })
                return {
                    'answer': response.content.strip(),
                    'confidence': 0.9,
                    'sources': ['对话上下文'],
                    'conversation_mode': True
                }
            else:
                prompt = self.qna_prompt
                chain = prompt | self.llm | self.output_parser
                result = chain.invoke({
                    "question": question,
                    "context": context,
                    "history": history
                })
                
                # 确保结果包含所有必要字段
                if isinstance(result, dict):
                    result['conversation_mode'] = conversation_mode
                    return result
                else:
                    return {
                        'answer': str(result),
                        'confidence': 0.8,
                        'sources': [],
                        'conversation_mode': conversation_mode
                    }
                    
        except Exception as e:
            return {
                'answer': f"抱歉，处理问题时出现错误: {str(e)}",
                'confidence': 0.0,
                'sources': [],
                'error': str(e),
                'conversation_mode': conversation_mode
            }
    
    def evaluate_answer_quality(self, question: str, answer: str, 
                              expected_answer: str = None) -> Dict[str, Any]:
        """评估回答质量
        
        Args:
            question: 原始问题
            answer: 给出的回答
            expected_answer: 期望的答案（可选）
        
        Returns:
            质量评估结果
        """
        try:
            evaluation_prompt = """
请评估以下问答的质量：

问题：{question}
回答：{answer}

请从以下维度进行评估（1-10分）：
1. 准确性：回答是否准确反映了问题
2. 完整性：回答是否全面覆盖了问题要点
3. 清晰度：回答是否易于理解
4. 相关性：回答是否与问题直接相关
5. 实用性：回答是否有实际价值

请给出每个维度的分数和简要说明。
"""
            
            prompt = ChatPromptTemplate.from_template(evaluation_prompt)
            chain = prompt | self.llm
            response = chain.invoke({
                "question": question,
                "answer": answer
            })
            
            # 解析评估结果
            content = response.content.strip()
            scores = re.findall(r'(\d+)\s*分', content)
            
            return {
                'evaluation': content,
                'accuracy': int(scores[0]) if len(scores) > 0 else 5,
                'completeness': int(scores[1]) if len(scores) > 1 else 5,
                'clarity': int(scores[2]) if len(scores) > 2 else 5,
                'relevance': int(scores[3]) if len(scores) > 3 else 5,
                'usefulness': int(scores[4]) if len(scores) > 4 else 5,
                'overall_score': sum([int(scores[i]) for i in range(min(5, len(scores)))]) / min(5, len(scores))
            }
            
        except Exception as e:
            return {
                'evaluation': f"评估失败: {str(e)}",
                'accuracy': 5,
                'completeness': 5,
                'clarity': 5,
                'relevance': 5,
                'usefulness': 5,
                'overall_score': 5,
                'error': str(e)
            }
    
    def generate_related_questions(self, question: str, context: str) -> List[str]:
        """生成相关问题
        
        Args:
            question: 原始问题
            context: 上下文信息
        
        Returns:
            相关问题列表
        """
        try:
            related_questions_prompt = """
基于以下问题和上下文，生成3-5个相关的问题：

原始问题：{question}
上下文：{context}

请生成与原始问题相关且有助于深入理解的问题。
"""
            
            prompt = ChatPromptTemplate.from_template(related_questions_prompt)
            chain = prompt | self.llm
            response = chain.invoke({
                "question": question,
                "context": context
            })
            
            # 解析生成的问题
            content = response.content.strip()
            questions = re.findall(r'\d+\.\s*(.+?)(?=\n|$)', content)
            
            return questions if questions else [
                f"关于{question}的更多细节是什么？",
                f"{question}的实际应用场景有哪些？",
                f"如何深入学习{question}相关的知识？"
            ]
            
        except Exception as e:
            return [
                f"关于{question}的更多细节是什么？",
                f"{question}的实际应用场景有哪些？",
                f"如何深入学习{question}相关的知识？"
            ]


# 全局问答Agent实例
qna_agent = None


def get_qna_agent():
    """获取问答Agent实例"""
    global qna_agent
    if qna_agent is None:
        qna_agent = QnAAgent()
    return qna_agent