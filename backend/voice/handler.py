from abc import ABC, abstractmethod
from typing import Dict, Any
import speech_recognition as sr
from gtts import gTTS
import os


class VoiceHandler(ABC):
    """语音处理器抽象基类"""
    
    @abstractmethod
    def speech_to_text(self, audio_path: str) -> str:
        """语音转文本"""
        pass
    
    @abstractmethod
    def text_to_speech(self, text: str, output_path: str) -> str:
        """文本转语音"""
        pass


class GTTSVoiceHandler(VoiceHandler):
    """基于gTTS的语音处理器"""
    
    def __init__(self, language: str = "zh-cn"):
        """初始化语音处理器
        
        Args:
            language: 语言代码，默认中文
        """
        self.language = language
        self.recognizer = sr.Recognizer()
    
    def speech_to_text(self, audio_path: str) -> str:
        """语音转文本
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            识别的文本
        """
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                return text
        except Exception as e:
            print(f"语音转文本失败: {e}")
            return ""
    
    def text_to_speech(self, text: str, output_path: str) -> str:
        """文本转语音
        
        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径
        
        Returns:
            输出音频文件路径
        """
        try:
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"文本转语音失败: {e}")
            return ""
    
    def real_time_speech_to_text(self) -> str:
        """实时语音转文本
        
        Returns:
            识别的文本
        """
        try:
            with sr.Microphone() as source:
                print("正在听...")
                audio_data = self.recognizer.listen(source)
                print("正在识别...")
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                return text
        except Exception as e:
            print(f"实时语音识别失败: {e}")
            return ""


class VoiceAssistant:
    """语音助手"""
    
    def __init__(self, voice_handler: VoiceHandler):
        """初始化语音助手
        
        Args:
            voice_handler: 语音处理器实例
        """
        self.voice_handler = voice_handler
    
    def process_audio_input(self, audio_path: str) -> Dict[str, Any]:
        """处理音频输入
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            处理结果
        """
        text = self.voice_handler.speech_to_text(audio_path)
        return {
            'original_audio': audio_path,
            'transcribed_text': text,
            'processing_status': 'success' if text else 'failed'
        }
    
    def generate_audio_response(self, text: str, output_dir: str = "./") -> Dict[str, Any]:
        """生成音频响应
        
        Args:
            text: 要转换的文本
            output_dir: 输出目录
        
        Returns:
            生成结果
        """
        # 生成唯一的输出文件名
        output_path = os.path.join(output_dir, f"response_{os.getpid()}_{time.time()}.mp3")
        audio_path = self.voice_handler.text_to_speech(text, output_path)
        
        return {
            'input_text': text,
            'audio_response': audio_path,
            'generation_status': 'success' if audio_path else 'failed'
        }
    
    def interactive_voice_session(self) -> Dict[str, Any]:
        """交互式语音会话
        
        Returns:
            会话结果
        """
        print("开始交互式语音会话...")
        print("请说话，说完后会自动识别...")
        
        user_input = self.voice_handler.real_time_speech_to_text()
        if not user_input:
            return {
                'status': 'failed',
                'message': '无法识别语音输入'
            }
        
        print(f"识别到: {user_input}")
        
        # 这里可以添加与大模型的交互逻辑
        # 暂时返回简单的响应
        response_text = f"您刚才说: {user_input}"
        
        # 生成音频响应
        output_path = f"response_{os.getpid()}_{time.time()}.mp3"
        audio_path = self.voice_handler.text_to_speech(response_text, output_path)
        
        return {
            'status': 'success',
            'user_input': user_input,
            'response_text': response_text,
            'response_audio': audio_path
        }


# 工具函数
import time

def generate_unique_filename(prefix: str = "audio", extension: str = "mp3") -> str:
    """生成唯一的文件名
    
    Args:
        prefix: 文件名前缀
        extension: 文件扩展名
    
    Returns:
        唯一的文件名
    """
    timestamp = int(time.time() * 1000)
    pid = os.getpid()
    return f"{prefix}_{pid}_{timestamp}.{extension}"

def cleanup_audio_files(directory: str, max_age: int = 3600):
    """清理旧的音频文件
    
    Args:
        directory: 要清理的目录
        max_age: 最大保留时间（秒）
    """
    current_time = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and filename.endswith(('.mp3', '.wav', '.ogg')):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age:
                try:
                    os.remove(file_path)
                    print(f"已清理旧音频文件: {file_path}")
                except Exception as e:
                    print(f"清理文件失败 {file_path}: {e}")
