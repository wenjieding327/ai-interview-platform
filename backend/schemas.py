from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class StartInterviewRequest(BaseModel):
    target_role: str = Field(..., min_length=1)


class InterviewStepRequest(BaseModel):
    target_role: str = Field(default="")
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class ScoreRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class FollowUpRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class SessionStepRequest(BaseModel):
    session_id: int
    answer: str = Field(..., min_length=1)
