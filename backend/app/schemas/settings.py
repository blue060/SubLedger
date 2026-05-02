from pydantic import BaseModel
from typing import Optional


class SettingsOut(BaseModel):
    preferred_currency: str
    reminder_days: int
    monthly_budget: Optional[float] = None
    theme: str = "light"
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_tls: bool = True
    bark_url: Optional[str] = None
    serverchan_key: Optional[str] = None


class SettingsUpdate(BaseModel):
    preferred_currency: Optional[str] = None
    reminder_days: Optional[int] = None
    monthly_budget: Optional[float] = None
    theme: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_tls: Optional[bool] = None
    bark_url: Optional[str] = None
    serverchan_key: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]