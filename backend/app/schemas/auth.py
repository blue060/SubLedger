from pydantic import BaseModel
from datetime import date, datetime


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    username: str
    token: str


class AuthStatus(BaseModel):
    user_id: int
    username: str