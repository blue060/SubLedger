from pydantic import BaseModel
from datetime import date, datetime


class LoginRequest(BaseModel):
    username: str = "admin"
    password: str


class SetupRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    token: str


class AuthStatus(BaseModel):
    user_id: int
    username: str