import re

from pydantic import BaseModel, Field, field_validator
from typing import Optional

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Invalid email format")
        return value


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Invalid email format")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=3000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty")
        return value


class StartInterviewRequest(BaseModel):
    target_role: str = Field(..., min_length=1, max_length=100)

    @field_validator("target_role")
    @classmethod
    def validate_target_role(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Target role cannot be empty")
        return value


class InterviewStepRequest(BaseModel):
    target_role: str = Field(default="")
    question: str = Field(..., min_length=1, max_length=3000)
    answer: str = Field(..., min_length=1, max_length=5000)


class ScoreRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=3000)
    answer: str = Field(..., min_length=1, max_length=5000)


class FollowUpRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=3000)
    answer: str = Field(..., min_length=1, max_length=5000)


class SessionStepRequest(BaseModel):
    session_id: int
    answer: str = Field(..., min_length=1, max_length=5000)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Answer cannot be empty")
        return value


class AgentToolRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=3000)
    question: Optional[str] = Field(default=None, max_length=3000)
    session_id: Optional[int] = None

    @field_validator("intent")
    @classmethod
    def validate_intent(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Intent cannot be empty")
        return value

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        value = value.strip()
        return value or None
