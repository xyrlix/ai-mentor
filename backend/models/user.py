from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class InterviewHistory(Base):
    """面试历史模型"""
    __tablename__ = "interview_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    interview_id = Column(String(100), unique=True, index=True, nullable=False)
    kb_id = Column(Integer, nullable=True)
    scene_type = Column(String(20), nullable=False)
    topic = Column(String(200), nullable=True)
    score = Column(Float, nullable=True)
    duration = Column(Integer, nullable=True)  # 面试时长（秒）
    status = Column(String(20),
                    default="completed")  # completed, in_progress, draft
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime,
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InterviewHistory(interview_id='{self.interview_id}', user_id='{self.user_id}', scene_type='{self.scene_type}')>"


class InterviewMessage(Base):
    """面试消息模型"""
    __tablename__ = "interview_messages"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(String(100), index=True, nullable=False)
    message_id = Column(Integer, nullable=False)  # 消息序号
    speaker = Column(String(20), nullable=False)  # interviewer, candidate
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<InterviewMessage(interview_id='{self.interview_id}', speaker='{self.speaker}')>"
