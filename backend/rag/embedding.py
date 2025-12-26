"""
嵌入模块：提供文本嵌入功能
支持多种嵌入模型，默认使用 BAAI/bge-large-zh-v1.5
"""
import os
import hashlib
from typing import List, Optional
import numpy as np
from config import settings
from utils.redis import redis_cache

# 延迟导入torch以加快启动速度
_torch_imported = False

def _get_torch():
    """延迟导入torch"""
    global _torch_imported
    if not _torch_imported:
        import torch
        globals()['torch'] = torch
        _torch_imported = True
        return torch
    return globals()['torch']

# 设置环境变量以优化速度
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# 使用新的 HF_HOME 环境变量（避免警告）
cache_dir = os.path.join(os.getcwd(), '.cache')
os.environ['HF_HOME'] = cache_dir
os.environ['HUGGINGFACE_HUB_CACHE'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = os.path.join(cache_dir, 'transformers')
os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(cache_dir, 'sentence_transformers')

# 确保缓存目录存在
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(os.path.join(cache_dir, 'transformers'), exist_ok=True)
os.makedirs(os.path.join(cache_dir, 'sentence_transformers'), exist_ok=True)

# 完全懒加载 - 只有在真正使用时才导入
_sentence_transformers_imported = False
_sentence_transformers_module = None

def _get_sentence_transformers():
    """获取sentence_transformers模块"""
    global _sentence_transformers_module, _sentence_transformers_imported
    if not _sentence_transformers_imported:
        import sentence_transformers
        _sentence_transformers_module = sentence_transformers
        _sentence_transformers_imported = True
    return _sentence_transformers_module


class EmbeddingModel:
    """嵌入模型类"""
    
    def __init__(self, model_name: str = None, device: str = "auto"):
        """初始化嵌入模型
        
        Args:
            model_name: 模型名称，默认使用配置中的模型
            device: 设备类型，"auto", "cpu", "cuda", "mps"
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = settings.VECTOR_DIMENSION
        
        # 自动选择设备
        if device == "auto":
            torch = _get_torch()  # 延迟导入
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
        
        # 延迟加载模型
        self._model = None
        self._model_loaded = False
    
    def _load_model(self):
        """延迟加载模型"""
        if not self._model_loaded:
            sentence_transformers = _get_sentence_transformers()  # 获取模块
            try:
                print(f"正在加载嵌入模型: {self.model_name}")
                
                # 简化加载参数，避免需要accelerate库
                self._model = sentence_transformers.SentenceTransformer(
                    self.model_name, 
                    device=self.device
                )
                self._model_loaded = True
                print(f"嵌入模型加载成功，设备: {self.device}")
            except Exception as e:
                print(f"嵌入模型加载失败: {e}")
                # 使用备用模型
                try:
                    fallback_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                    print(f"尝试使用备用模型: {fallback_model}")
                    sentence_transformers = _get_sentence_transformers()
                    self._model = sentence_transformers.SentenceTransformer(fallback_model, device=self.device)
                    self.model_name = fallback_model
                    self.dimension = 384  # MiniLM-L12-v2 的维度
                    self._model_loaded = True
                    print(f"备用模型加载成功")
                except Exception as fallback_error:
                    print(f"备用模型也加载失败: {fallback_error}")
                    raise RuntimeError(f"无法加载任何嵌入模型: {e}, {fallback_error}")
    
    def embed_query(self, text: str) -> List[float]:
        """为单个查询文本生成嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        # 生成缓存键
        cache_key = f"embedding_query:{hashlib.md5(f"{self.model_name}:{text}".encode()).hexdigest()}"
        
        # 尝试从缓存获取
        cached_embedding = redis_cache.get(cache_key)
        if cached_embedding:
            return cached_embedding
        
        # 确保模型已加载
        if not self._model_loaded:
            self._load_model()
        
        try:
            # 生成嵌入
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            # 转换为列表
            embedding_list = embedding.tolist()
            
            # 存入缓存（1小时）
            redis_cache.set(cache_key, embedding_list, expire=3600)
            
            return embedding_list
            
        except Exception as e:
            print(f"生成嵌入向量失败: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为多个文档文本生成嵌入向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            嵌入向量列表
        """
        if not texts:
            return []
        
        # 批量处理可以提高效率
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 为当前批次生成缓存键
            batch_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for j, text in enumerate(batch_texts):
                cache_key = f"embedding_doc:{hashlib.md5(f'{self.model_name}:{text}'.encode()).hexdigest()}"
                cached_embedding = redis_cache.get(cache_key)
                
                if cached_embedding:
                    batch_embeddings.append(cached_embedding)
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(j)
            
            # 处理未缓存的文本
            if uncached_texts:
                # 确保模型已加载
                if not self._model_loaded:
                    self._load_model()
                
                try:
                    # 批量生成嵌入
                    new_embeddings = self._model.encode(uncached_texts, convert_to_numpy=True)
                    
                    # 将新嵌入缓存并添加到批次结果中
                    for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                        embedding_list = embedding.tolist()
                        batch_embeddings.insert(idx, embedding_list)
                        
                        # 缓存单个嵌入
                        cache_key = f"embedding_doc:{hashlib.md5(f'{self.model_name}:{text}'.encode()).hexdigest()}"
                        redis_cache.set(cache_key, embedding_list, expire=3600)
                        
                except Exception as e:
                    print(f"批量生成嵌入向量失败: {e}")
                    raise
            
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def get_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": self.device,
            "loaded": self._model_loaded
        }


# 全局模型实例
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    """获取嵌入模型实例
    
    Returns:
        嵌入模型实例
    """
    global _embedding_model
    
    if _embedding_model is None:
        try:
            _embedding_model = EmbeddingModel()
        except Exception as e:
            print(f"创建嵌入模型失败: {e}")
            raise RuntimeError(f"无法创建嵌入模型: {e}")
    
    return _embedding_model


def create_embedding_model(model_name: str = None, device: str = "auto") -> EmbeddingModel:
    """创建新的嵌入模型实例
    
    Args:
        model_name: 模型名称
        device: 设备类型
        
    Returns:
        新的嵌入模型实例
    """
    return EmbeddingModel(model_name=model_name, device=device)


def clear_embedding_cache():
    """清除嵌入相关的缓存"""
    # 这里可以添加清除缓存的逻辑
    # 目前 redis_cache 没有提供按模式删除的功能
    pass


# 预定义的常用模型
EMBEDDING_MODELS = {
    "bge_large_zh": "BAAI/bge-large-zh-v1.5",
    "bge_base_zh": "BAAI/bge-base-zh-v1.5",
    "bge_small_zh": "BAAI/bge-small-zh-v1.5",
    "multilingual_minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "all_minilm_l6": "sentence-transformers/all-MiniLM-L6-v2",
    "all_mpnet_base": "sentence-transformers/all-mpnet-base-v2"
}


def get_available_models() -> dict:
    """获取可用的嵌入模型列表"""
    return EMBEDDING_MODELS.copy()


def validate_model_name(model_name: str) -> bool:
    """验证模型名称是否有效"""
    # 检查是否在预定义列表中
    if model_name in EMBEDDING_MODELS.values():
        return True
    
    # 检查是否是有效的 huggingface 模型格式
    if "/" in model_name and len(model_name.split("/")) == 2:
        return True
    
    return False