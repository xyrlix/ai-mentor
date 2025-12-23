from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """创建用户模型"""
    password: str


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class InterviewHistoryBase(BaseModel):
    """面试历史基础模型"""
    interview_id: str
    kb_id: Optional[int] = None
    scene_type: str
    topic: Optional[str] = None


class InterviewHistoryCreate(InterviewHistoryBase):
    """创建面试历史模型"""
    pass


class InterviewHistoryResponse(InterviewHistoryBase):
    """面试历史响应模型"""
    id: int
    user_id: int
    score: Optional[float] = None
    duration: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InterviewMessageBase(BaseModel):
    """面试消息基础模型"""
    interview_id: str
    message_id: int
    speaker: str
    content: str


class InterviewMessageCreate(InterviewMessageBase):
    """创建面试消息模型"""
    pass


class InterviewMessageResponse(InterviewMessageBase):
    """面试消息响应模型"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
