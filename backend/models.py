from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    histories = relationship("InterviewHistory", back_populates="user")


class InterviewHistory(Base):
    __tablename__ = "interview_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    target_role = Column(String(255), default="")
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    evaluation = Column(Text, default="")
    followup_question = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="histories")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    target_role = Column(String(255), default="")
    status = Column(String(50), default="active")

    current_question = Column(Text, default="")
    turns_json = Column(Text, default="[]")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
