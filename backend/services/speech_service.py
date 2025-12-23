import azure.cognitiveservices.speech as speechsdk
from typing import Optional
from config import settings


class SpeechService:
    """语音服务类，封装了语音转文本和文本转语音功能"""
    
    def __init__(self):
        """初始化语音服务"""
        self.speech_config = None
        if settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            self.speech_config.speech_recognition_language = settings.AZURE_SPEECH_LANGUAGE
            self.speech_config.speech_synthesis_language = settings.AZURE_SPEECH_LANGUAGE
            self.speech_config.speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"
    
    def speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """语音转文本
        
        Args:
            audio_file_path: 音频文件路径
        
        Returns:
            识别出的文本，如果识别失败则返回None
        """
        if not self.speech_config:
            raise Exception("Azure Speech Service未配置")
        
        try:
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # 开始识别
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                return None
            return None
        except Exception as e:
            raise Exception(f"语音转文本失败: {str(e)}")
    
    def text_to_speech(self, text: str, output_file_path: str) -> bool:
        """文本转语音
        
        Args:
            text: 要转换的文本
            output_file_path: 输出音频文件路径
        
        Returns:
            是否转换成功
        """
        if not self.speech_config:
            raise Exception("Azure Speech Service未配置")
        
        try:
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file_path)
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # 开始合成
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                raise Exception(f"文本转语音失败: {cancellation_details.reason}")
            return False
        except Exception as e:
            raise Exception(f"文本转语音失败: {str(e)}")
    
    async def speech_to_text_stream(self, audio_data: bytes) -> Optional[str]:
        """流式语音转文本
        
        Args:
            audio_data: 音频数据
        
        Returns:
            识别出的文本，如果识别失败则返回None
        """
        # 简化实现，实际项目中应使用流式识别
        import tempfile
        import os
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_file_path = f.name
        
        try:
            return self.speech_to_text(temp_file_path)
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)
    
    async def text_to_speech_stream(self, text: str) -> Optional[bytes]:
        """流式文本转语音
        
        Args:
            text: 要转换的文本
        
        Returns:
            音频数据，如果转换失败则返回None
        """
        # 简化实现，实际项目中应使用流式合成
        import tempfile
        import os
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file_path = f.name
        
        try:
            success = self.text_to_speech(text, temp_file_path)
            if success:
                with open(temp_file_path, "rb") as f:
                    return f.read()
            return None
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)


# 创建语音服务实例
speech_service = SpeechService()
