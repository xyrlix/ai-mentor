import os
import asyncio
import tempfile
from typing import Optional, AsyncGenerator
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.audio import AudioConfig

from config import settings


class EnhancedSpeechService:
    """增强版语音服务"""
    
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # 设置语言（中文）
        self.speech_config.speech_synthesis_language = "zh-CN"
        self.speech_config.speech_recognition_language = "zh-CN"
        
        # 设置语音合成声音
        self.speech_config.speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"
    
    async def text_to_speech(self, text: str, output_file: Optional[str] = None) -> bytes:
        """文本转语音
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径（可选）
            
        Returns:
            音频数据
        """
        try:
            # 创建语音合成器
            if output_file:
                audio_config = AudioConfig(filename=output_file)
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.speech_config, 
                    audio_config=audio_config
                )
            else:
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.speech_config
                )
            
            # 执行语音合成
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                if output_file:
                    return b""  # 文件已保存到指定路径
                else:
                    return result.audio_data
            else:
                raise Exception(f"语音合成失败: {result.reason}")
                
        except Exception as e:
            raise Exception(f"语音合成错误: {str(e)}")
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """语音转文本
        
        Args:
            audio_data: 音频数据
            
        Returns:
            识别的文本
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # 创建音频配置
                audio_config = AudioConfig(filename=temp_file_path)
                
                # 创建语音识别器
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config, 
                    audio_config=audio_config
                )
                
                # 执行语音识别
                result = recognizer.recognize_once_async().get()
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    return result.text
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    raise Exception("无法识别语音")
                else:
                    raise Exception(f"语音识别失败: {result.reason}")
                    
            finally:
                # 删除临时文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise Exception(f"语音识别错误: {str(e)}")
    
    async def stream_speech_to_text(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        """流式语音转文本
        
        Args:
            audio_stream: 音频流生成器
            
        Yields:
            识别的文本片段
        """
        try:
            # 创建推流识别器
            push_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = AudioConfig(stream=push_stream)
            
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # 设置识别事件处理
            def recognized_handler(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    yield evt.result.text
            
            recognizer.recognized.connect(recognized_handler)
            
            # 开始连续识别
            recognizer.start_continuous_recognition_async()
            
            # 处理音频流
            async for audio_chunk in audio_stream:
                push_stream.write(audio_chunk)
                
                # 这里需要更复杂的逻辑来处理实时识别结果
                # 简化实现：等待识别完成
                await asyncio.sleep(0.1)
            
            # 停止识别
            recognizer.stop_continuous_recognition_async()
            
        except Exception as e:
            yield f"语音识别错误: {str(e)}"
    
    async def stream_text_to_speech(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """流式文本转语音
        
        Args:
            text_stream: 文本流生成器
            
        Yields:
            音频数据片段
        """
        try:
            # 创建推流合成器
            push_stream = speechsdk.audio.PushAudioOutputStream()
            audio_config = AudioConfig(stream=push_stream)
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # 处理文本流
            async for text_chunk in text_stream:
                if text_chunk.strip():
                    # 合成语音
                    result = synthesizer.speak_text_async(text_chunk).get()
                    
                    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                        yield result.audio_data
                    else:
                        yield b""  # 合成失败
            
        except Exception as e:
            yield b""  # 错误处理
    
    def get_available_voices(self) -> list:
        """获取可用的语音列表"""
        try:
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = synthesizer.get_voices_async().get()
            
            voices = []
            for voice in result.voices:
                if "zh-" in voice.locale.lower():
                    voices.append({
                        "name": voice.short_name,
                        "locale": voice.locale,
                        "gender": voice.gender.name,
                        "description": voice.local_name
                    })
            
            return voices
            
        except Exception as e:
            return [{
                "name": "zh-CN-XiaoxiaoNeural",
                "locale": "zh-CN", 
                "gender": "Female",
                "description": "晓晓（中文普通话）"
            }]
    
    def set_voice(self, voice_name: str):
        """设置语音合成声音"""
        self.speech_config.speech_synthesis_voice_name = voice_name
    
    def set_language(self, language: str):
        """设置语言"""
        self.speech_config.speech_synthesis_language = language
        self.speech_config.speech_recognition_language = language
    
    async def voice_interview(self, question: str, audio_response: bytes) -> dict:
        """语音面试处理
        
        Args:
            question: 面试问题
            audio_response: 用户语音回答
            
        Returns:
            面试结果
        """
        try:
            # 1. 语音转文本
            user_answer = await self.speech_to_text(audio_response)
            
            # 2. 分析回答（这里需要集成面试Agent）
            # 简化实现
            analysis = {
                "score": 8.0,
                "feedback": "回答清晰，表达流畅",
                "suggestions": ["可以更详细地阐述技术细节"]
            }
            
            # 3. 生成下一个问题
            next_question = "请继续谈谈您的项目经验"
            
            # 4. 文本转语音（下一个问题）
            next_question_audio = await self.text_to_speech(next_question)
            
            return {
                "user_answer_text": user_answer,
                "analysis": analysis,
                "next_question": next_question,
                "next_question_audio": next_question_audio.hex(),  # 转换为十六进制字符串便于传输
                "success": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def get_enhanced_speech_service() -> EnhancedSpeechService:
    """获取增强语音服务实例"""
    return EnhancedSpeechService()