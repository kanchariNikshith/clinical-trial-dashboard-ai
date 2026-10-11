"""User and Authentication schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from backend.app.core.security import validate_password_strength


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User plaintext password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        err = validate_password_strength(v)
        if err:
            raise ValueError(err)
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User plaintext password")


class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
