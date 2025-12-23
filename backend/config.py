from pydantic_settings import BaseSettings
from typing import Optional, Dict
import os


class Settings(BaseSettings):
    """应用配置类"""

    # 基本配置
    APP_NAME: str = "AI Mentor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置 - 使用PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres1688@localhost:5432/ai_mentor"

    # 大模型配置（优先国产）
    LLM_PROVIDER: str = "qwen"  # qwen / deepseek / zhipu / openai

    # 各模型API配置
    QWEN_API_KEY: Optional[str] = None
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-max"

    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_API_BASE: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_MODEL: str = "glm-4"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # 大模型通用配置
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # 向量模型配置（开源，无需API）
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384  # all-MiniLM-L6-v2 输出维度

    # 文档处理配置
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100

    # 语音配置
    VOICE_LANGUAGE: str = "zh-cn"
    VOICE_RATE: float = 1.0
    WHISPER_MODEL: str = "base"
    AZURE_TTS_KEY: Optional[str] = None
    AZURE_TTS_REGION: str = "eastasia"

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".pptx"}

    # API配置
    API_V1_STR: str = "/api"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-here-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 速率限制配置
    RATE_LIMIT: int = 100  # 每分钟请求数

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 缓存配置
    CACHE_EXPIRE_MINUTES: int = 30

    # 支付系统配置
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID: Optional[str] = None
    STRIPE_SUCCESS_URL: str = "http://localhost/success"
    STRIPE_CANCEL_URL: str = "http://localhost/cancel"

    # Azure Speech Service 配置
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: str = "eastasia"
    AZURE_SPEECH_LANGUAGE: str = "zh-CN"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"  # 指定使用UTF-8编码读取.env文件
        case_sensitive = True
        extra = "allow"


# 创建配置实例
settings = Settings()

# 大模型配置字典，方便在代码中使用
LLM_CONFIG: Dict[str, any] = {
    "provider": settings.LLM_PROVIDER,
    "temperature": settings.LLM_TEMPERATURE,
    "max_tokens": settings.LLM_MAX_TOKENS,
    "qwen_api_key": settings.QWEN_API_KEY,
    "qwen_api_base": settings.QWEN_API_BASE,
    "qwen_model": settings.QWEN_MODEL,
    "deepseek_api_key": settings.DEEPSEEK_API_KEY,
    "deepseek_api_base": settings.DEEPSEEK_API_BASE,
    "deepseek_model": settings.DEEPSEEK_MODEL,
    "zhipu_api_key": settings.ZHIPU_API_KEY,
    "zhipu_api_base": settings.ZHIPU_API_BASE,
    "zhipu_model": settings.ZHIPU_MODEL,
    "openai_api_key": settings.OPENAI_API_KEY,
    "openai_api_base": settings.OPENAI_API_BASE,
    "openai_model": settings.OPENAI_MODEL,
}

# 语音配置字典
VOICE_CONFIG: Dict[str, any] = {
    "whisper_model": settings.WHISPER_MODEL,
    "azure_tts_key": settings.AZURE_TTS_KEY,
    "azure_tts_region": settings.AZURE_TTS_REGION,
}
