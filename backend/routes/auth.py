from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from models import User
from schemas.auth import UserCreate, UserResponse, Token, InterviewHistoryResponse, InterviewMessageResponse
from utils.auth import verify_password, get_password_hash, create_access_token
from config import settings
from database import get_db


router = APIRouter(prefix="/api/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from jose import jwt
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被使用"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(get_current_admin_user)])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取用户列表（管理员）"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/interview-history", response_model=List[InterviewHistoryResponse])
async def get_interview_history(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """获取当前用户的面试历史"""
    from models import InterviewHistory
    histories = db.query(InterviewHistory).filter(InterviewHistory.user_id == current_user.id).order_by(InterviewHistory.created_at.desc()).all()
    return histories


@router.get("/interview-history/{interview_id}/messages", response_model=List[InterviewMessageResponse])
async def get_interview_messages(interview_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """获取面试消息"""
    from models import InterviewHistory, InterviewMessage
    # 验证面试历史属于当前用户
    history = db.query(InterviewHistory).filter(
        InterviewHistory.interview_id == interview_id,
        InterviewHistory.user_id == current_user.id
    ).first()
    if not history:
        raise HTTPException(status_code=404, detail="面试历史不存在或不属于当前用户")
    
    messages = db.query(InterviewMessage).filter(
        InterviewMessage.interview_id == interview_id
    ).order_by(InterviewMessage.message_id).all()
    return messages
