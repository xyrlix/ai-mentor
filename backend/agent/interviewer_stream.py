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
                               context: str, question: str = None) -> AsyncGenerator[str, None]:
    """流式调用大模型，yield 单个 token
    
    Args:
        scene_type: 场景类型 (it/language/cert)
        user_answer: 用户回答
        context: RAG检索到的上下文
        question: 当前问题（可选）
    
    Yields:
        单个 token 字符串
    """
    print(f"run_interview_stream 被调用: scene_type={scene_type}, user_answer={user_answer}")
    
    provider = LLM_CONFIG["provider"]
    print(f"使用provider: {provider}")

    # 构建完整提示（不使用复杂的模板，直接构建）
    base_template = """你是一位专业的{scene_type}领域面试官。

上下文信息：
{context}

历史对话：
{history}

上一个问题：
{question}

候选人回答：
{user_answer}

请根据候选人的回答，给出：
1. 对回答的简短评价
2. 一个自然的后续问题

请以对话的形式回复，不要包含评分格式。
"""

    # 生成问题 - 根据场景类型和上下文
    if not question:
        if user_answer and user_answer.startswith("我是"):
            question = f"基于{get_role(scene_type)}的岗位要求，请详细介绍你的相关经验和技能"
        else:
            question = "请介绍一下你的背景和经验"
    
    prompt = base_template.format(
        scene_type=get_role(scene_type),
        context=context or "无特定上下文",
        history="",
        question=question,
        user_answer=user_answer
    )
    
    print(f"生成的prompt长度: {len(prompt)}")

    try:
        print(f"检查API密钥配置，provider: {provider}")
        
        # 检查是否有可用的API密钥
        has_api_key = False
        if provider == "qwen" and LLM_CONFIG.get("qwen_api_key"):
            has_api_key = True
        elif provider == "deepseek" and LLM_CONFIG.get("deepseek_api_key"):
            has_api_key = True
        elif provider == "zhipu" and LLM_CONFIG.get("zhipu_api_key"):
            has_api_key = True
        elif provider == "openai" and LLM_CONFIG.get("openai_api_key"):
            has_api_key = True
        
        print(f"has_api_key: {has_api_key}")
        
        if not has_api_key:
            print(f"警告: {provider} API密钥未配置，使用模拟响应")
            print("开始模拟流式响应...")
            async for token in run_mock_stream(prompt):
                yield token
        elif provider == "qwen":
            # 阿里云通义千问流式调用
            print("使用通义千问API")
            async for token in run_qwen_stream(prompt):
                yield token
        elif provider == "deepseek":
            # 深度求索流式调用
            print("使用深度求索API")
            async for token in run_deepseek_stream(prompt):
                yield token
        elif provider == "zhipu":
            # 智谱AI流式调用
            print("使用智谱AI API")
            async for token in run_zhipu_stream(prompt):
                yield token
        elif provider == "openai":
            # OpenAI流式调用
            print("使用OpenAI API")
            async for token in run_openai_stream(prompt):
                yield token
        else:
            # 默认返回模拟流式响应
            print(f"未知provider {provider}，使用模拟响应")
            async for token in run_mock_stream(prompt):
                yield token
    except Exception as e:
        print(f"流式调用失败: {e}")
        import traceback
        traceback.print_exc()
        # 如果API调用失败，使用模拟响应
        print("回退到模拟响应")
        async for token in run_mock_stream(prompt):
            yield token


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
        print(f"通义千问API请求URL: {LLM_CONFIG['qwen_api_base']}")
        print(f"请求头: {headers}")
        print(f"请求体: {payload}")
        
        async with client.stream("POST",
                                 LLM_CONFIG['qwen_api_base'],
                                 headers=headers,
                                 json=payload) as response:
            print(f"API响应状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            
            async for line in response.aiter_lines():
                if line:
                    print(f"原始响应行: {line}")
                    
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
                        print(f"无法解析的数据: {data_str}")
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
    """模拟流式响应，基于prompt内容生成相关回复"""
    print(f"开始模拟流式响应，prompt长度: {len(prompt)}")
    
    # 从prompt中提取关键信息
    user_answer = ""
    context = ""
    if "候选人回答：" in prompt:
        user_answer = prompt.split("候选人回答：")[1].strip()
    if "上下文信息：" in prompt and "历史对话：" in prompt:
        context = prompt.split("上下文信息：")[1].split("历史对话：")[0].strip()
    
    # 根据用户回答和上下文生成相关的模拟回复
    mock_response = generate_contextual_response(user_answer, context)
    
    print(f"模拟响应长度: {len(mock_response)}")
    
    for i, char in enumerate(mock_response):
        yield char
        # 模拟打字速度
        import asyncio
        await asyncio.sleep(0.03)  # 稍微快一点
        if i % 30 == 0:  # 每30个字符打印一次进度
            print(f"模拟输出进度: {i+1}/{len(mock_response)}")
    
    print("模拟流式响应完成")


def generate_contextual_response(user_answer: str, context: str) -> str:
    """根据用户回答和上下文生成智能回复"""
    
    # 分析用户回答中的关键词
    keywords = []
    if any(tech in user_answer.lower() for tech in ['python', 'java', 'javascript', 'go', 'rust']):
        keywords.append('编程语言')
    if any(framework in user_answer.lower() for framework in ['django', 'flask', 'react', 'vue', 'spring']):
        keywords.append('框架')
    if any(exp in user_answer.lower() for exp in ['年', '经验', '项目', '工作', '实习']):
        keywords.append('经验')
    if any(skill in user_answer.lower() for skill in ['数据库', 'mysql', 'mongodb', 'redis', '算法']):
        keywords.append('技术栈')
    
    # 基于上下文生成问题
    if context and len(context) > 50:
        # 如果有相关文档上下文，基于文档内容提问
        if 'java' in context.lower():
            question = "您在Java开发中最熟悉哪些设计模式？能结合具体项目说明一下吗？"
        elif 'python' in context.lower():
            question = "在Python项目中，您是如何进行性能优化的？有没有使用过异步编程？"
        elif '前端' in context or 'react' in context.lower() or 'vue' in context.lower():
            question = "在前端开发中，您是如何处理状态管理和组件通信的？"
        else:
            question = "基于您提供的背景，能否深入谈谈您在项目中的具体职责和技术贡献？"
    else:
        # 根据用户回答的关键词生成问题
        if '编程语言' in keywords and '经验' in keywords:
            question = "听起来您有多语言开发经验，您是如何选择适合不同项目的技术栈的？"
        elif '框架' in keywords:
            question = "在使用这些框架时，您遇到过哪些性能或架构方面的挑战？"
        elif '经验' in keywords:
            question = "能否分享一个您在职业生涯中解决的最具挑战性的技术问题？"
        else:
            question = "感谢您的介绍！接下来能否详细谈谈您的技术专长和项目经验？"
    
    return f"""感谢您的回答！

{question}

这将帮助我更好地了解您的技术能力和解决问题的思路。"""


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
    # 生成固定的模拟回复，避免重复调用流式函数
    follow_up = """感谢您的介绍！听起来您在Python开发方面有不错的经验。

我想进一步了解一下：您在Python开发中主要使用哪些框架？比如Django、Flask还是FastAPI？能否分享一个您最近完成的项目中遇到的挑战以及您是如何解决的？"""

    # 简化处理：基于回答长度给出简单评分
    answer_length = len(user_answer)
    if answer_length < 10:
        score = 3.0
        comment = "回答过于简短，建议提供更多细节"
    elif answer_length < 50:
        score = 6.0
        comment = "回答基本完整，可以更深入一些"
    else:
        score = 8.0
        comment = "回答详细，内容充实"

    return {
        "score": score,
        "follow_up": follow_up.strip(),
        "comment": comment
    }
