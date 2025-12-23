from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
import os
from typing import Optional
import tempfile

from services.speech_service import speech_service
from routes.auth import get_current_active_user
from models import User

router = APIRouter(prefix="/api/speech", tags=["语音服务"])


@router.post("/speech-to-text")
async def speech_to_text(
        audio_file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user)):
    """语音转文本
    
    Args:
        audio_file: 音频文件，支持WAV、MP3等格式
    
    Returns:
        识别出的文本
    """
    try:
        # 检查文件类型
        allowed_extensions = [".wav", ".mp3", ".ogg"]
        file_ext = os.path.splitext(audio_file.filename or "")[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型，仅允许: {', '.join(allowed_extensions)}")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as f:
            f.write(await audio_file.read())
            temp_file_path = f.name

        try:
            # 调用语音转文本服务
            text = speech_service.speech_to_text(temp_file_path)
            if not text:
                raise HTTPException(status_code=400, detail="语音识别失败")

            return {"status": "success", "text": text}
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音转文本失败: {str(e)}")


@router.post("/text-to-speech")
async def text_to_speech(
    text: str, current_user: User = Depends(get_current_active_user)):
    """文本转语音
    
    Args:
        text: 要转换的文本
    
    Returns:
        音频文件流
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file_path = f.name

        try:
            # 调用文本转语音服务
            success = speech_service.text_to_speech(text, temp_file_path)
            if not success:
                raise HTTPException(status_code=500, detail="文本转语音失败")

            # 读取音频文件
            def iterfile():
                with open(temp_file_path, "rb") as f:
                    yield f.read()

            return StreamingResponse(iterfile(),
                                     media_type="audio/wav",
                                     headers={
                                         "Content-Disposition":
                                         f"attachment; filename=speech.wav"
                                     })
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本转语音失败: {str(e)}")


@router.post("/health")
async def speech_health_check(
        current_user: User = Depends(get_current_active_user)):
    """检查语音服务健康状态"""
    try:
        # 简化实现，检查配置是否完成
        from config import settings
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return {
                "status": "warning",
                "message": "Azure Speech Service未配置",
                "configured": False
            }

        return {
            "status": "success",
            "message": "Azure Speech Service已配置",
            "configured": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"健康检查失败: {str(e)}",
            "configured": False
        }
