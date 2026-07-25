from pydantic import BaseModel
from datetime import date, datetime


class LoginRequest(BaseModel):
    username: str = "admin"
    password: str


class LoginResponse(BaseModel):
    username: str


class AuthStatus(BaseModel):
    user_id: int
    username: str
