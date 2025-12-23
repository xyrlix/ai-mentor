import httpx
import json
from typing import AsyncGenerator, Dict, Any
from config import LLM_CONFIG
from .prompt_templates import get_prompt_template


def get_role(scene_type: str) -> str:
    """根据场景类型获取对应的角色描述"""
    role_map = {'it': '资深IT技术面试官', 'language': '专业小语种口语教练', 'cert': '职业考证专家'}
    return role_map.get(scene_type, '资深面试官')


async def run_interview_stream(scene_type: str, user_answer: str,
                               context: str) -> AsyncGenerator[str, None]:
    """流式调用大模型，yield 单个 token
    
    Args:
        scene_type: 场景类型 (it/language/cert)
        user_answer: 用户回答
        context: RAG检索到的上下文
    
    Yields:
        单个 token 字符串
    """
    provider = LLM_CONFIG["provider"]

    # 获取场景对应的提示模板
    prompt_template = get_prompt_template(scene_type)

    # 构建完整提示
    prompt = prompt_template.format(history="",
                                    context=context,
                                    question="上一个问题",
                                    user_answer=user_answer)

    try:
        if provider == "qwen":
            # 阿里云通义千问流式调用
            async for token in run_qwen_stream(prompt):
                yield token
        elif provider == "deepseek":
            # 深度求索流式调用
            async for token in run_deepseek_stream(prompt):
                yield token
        elif provider == "zhipu":
            # 智谱AI流式调用
            async for token in run_zhipu_stream(prompt):
                yield token
        elif provider == "openai":
            # OpenAI流式调用
            async for token in run_openai_stream(prompt):
                yield token
        else:
            # 默认返回模拟流式响应
            async for token in run_mock_stream(prompt):
                yield token
    except Exception as e:
        print(f"流式调用失败: {e}")
        yield "抱歉，系统出错了。"


async def run_qwen_stream(prompt: str) -> AsyncGenerator[str, None]:
    """调用通义千问流式接口"""
    headers = {
        "Authorization": f"Bearer {LLM_CONFIG['qwen_api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_CONFIG["qwen_model"],
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "stream": True,
        "temperature": LLM_CONFIG["temperature"],
        "max_tokens": LLM_CONFIG["max_tokens"]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST",
                                 LLM_CONFIG["qwen_api_base"],
                                 headers=headers,
                                 json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (KeyError, json.JSONDecodeError) as e:
                        print(f"解析通义千问响应失败: {e}")
                        continue


async def run_deepseek_stream(prompt: str) -> AsyncGenerator[str, None]:
    """调用深度求索流式接口"""
    headers = {
        "Authorization": f"Bearer {LLM_CONFIG['deepseek_api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_CONFIG["deepseek_model"],
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "stream": True,
        "temperature": LLM_CONFIG["temperature"],
        "max_tokens": LLM_CONFIG["max_tokens"]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST",
                                 LLM_CONFIG["deepseek_api_base"],
                                 headers=headers,
                                 json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (KeyError, json.JSONDecodeError) as e:
                        print(f"解析深度求索响应失败: {e}")
                        continue


async def run_zhipu_stream(prompt: str) -> AsyncGenerator[str, None]:
    """调用智谱AI流式接口"""
    headers = {
        "Authorization": f"Bearer {LLM_CONFIG['zhipu_api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_CONFIG["zhipu_model"],
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "stream": True,
        "temperature": LLM_CONFIG["temperature"],
        "max_tokens": LLM_CONFIG["max_tokens"]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST",
                                 LLM_CONFIG["zhipu_api_base"],
                                 headers=headers,
                                 json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (KeyError, json.JSONDecodeError) as e:
                        print(f"解析智谱AI响应失败: {e}")
                        continue


async def run_openai_stream(prompt: str) -> AsyncGenerator[str, None]:
    """调用OpenAI流式接口"""
    headers = {
        "Authorization": f"Bearer {LLM_CONFIG['openai_api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_CONFIG["openai_model"],
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "stream": True,
        "temperature": LLM_CONFIG["temperature"],
        "max_tokens": LLM_CONFIG["max_tokens"]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST",
                                 LLM_CONFIG["openai_api_base"],
                                 headers=headers,
                                 json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (KeyError, json.JSONDecodeError) as e:
                        print(f"解析OpenAI响应失败: {e}")
                        continue


async def run_mock_stream(prompt: str) -> AsyncGenerator[str, None]:
    """模拟流式响应，用于测试"""
    mock_response = "这是一个模拟的流式响应，用于测试系统功能。在实际部署中，这里会返回真实的大模型输出。"
    for char in mock_response:
        yield char
        # 模拟打字速度
        await httpx.AsyncClient().aclose()
        import asyncio
        await asyncio.sleep(0.03)


async def get_full_response(scene_type: str, user_answer: str,
                            context: str) -> Dict[str, Any]:
    """获取完整响应，包含评分和评论
    
    Args:
        scene_type: 场景类型
        user_answer: 用户回答
        context: 上下文
    
    Returns:
        包含评分、后续问题和评论的字典
    """
    # 先获取完整响应文本
    full_response = ""
    async for token in run_interview_stream(scene_type, user_answer, context):
        full_response += token

    # 简单解析，实际项目中可能需要更复杂的解析逻辑
    # 假设响应格式为：score\nfollow_up\ncomment
    parts = full_response.strip().split("\n")

    return {
        "score": float(parts[0].strip()) if parts else 0.0,
        "follow_up": parts[1].strip() if len(parts) > 1 else "",
        "comment": "\n".join(parts[2:]) if len(parts) > 2 else ""
    }
