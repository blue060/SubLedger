from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=12, max_length=128)
    is_admin: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            raise ValueError("用户名不能为空")
        if any(char.isspace() for char in username):
            raise ValueError("用户名不能包含空格")
        return username


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)
