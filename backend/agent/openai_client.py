import httpx
import json
import os
from typing import Any, Dict, List, Optional
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage

# 禁用环境变量中的代理设置
def disable_proxy():
    proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    for var in proxy_env_vars:
        os.environ.pop(var, None)

# 初始化时禁用代理
disable_proxy()

class OpenAIClient(Runnable):
    """直接调用OpenAI兼容API的客户端类，模拟langchain_openai.ChatOpenAI接口"""
    
    def __init__(self, api_key, api_base, model, temperature=0.7, max_tokens=2000):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_messages(self, prompt):
        """将各种格式的prompt转换为API需要的messages格式"""
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        elif hasattr(prompt, "to_messages"):
            # 处理ChatPromptTemplate类型的prompt
            return prompt.to_messages()
        elif isinstance(prompt, dict) and "messages" in prompt:
            return prompt["messages"]
        else:
            # 如果是其他格式，尝试直接作为内容
            return [{"role": "user", "content": str(prompt)}]
    
    def invoke(self, prompt, **kwargs):
        """调用API并返回响应，模拟ChatOpenAI的invoke方法"""
        try:
            # 构建请求体
            messages = self.generate_messages(prompt)
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # 添加额外参数
            if kwargs:
                payload.update(kwargs)
            
            # 发送请求
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
            
            response.raise_for_status()
            response_data = response.json()
            
            # 解析响应，模拟ChatOpenAI的返回格式
            class Response:
                def __init__(self, content):
                    self.content = content
            
            return Response(response_data["choices"][0]["message"]["content"])
            
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            raise
    
    async def ainvoke(self, prompt, **kwargs):
        """异步调用API（如果需要）"""
        try:
            messages = self.generate_messages(prompt)
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            if kwargs:
                payload.update(kwargs)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
            
            response.raise_for_status()
            response_data = response.json()
            
            class Response:
                def __init__(self, content):
                    self.content = content
            
            return Response(response_data["choices"][0]["message"]["content"])
            
        except Exception as e:
            print(f"异步API调用失败: {str(e)}")
            raise
    
    def predict(self, input, **kwargs):
        """预测方法，兼容ConversationChain的使用方式"""
        return self.invoke(input, **kwargs).content

# 工厂函数，用于创建不同模型的客户端
def create_llm(provider, api_key, api_base, model, temperature=0.7):
    """创建并返回对应的LLM客户端"""
    return OpenAIClient(
        api_key=api_key,
        api_base=api_base,
        model=model,
        temperature=temperature
    )
