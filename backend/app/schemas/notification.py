from pydantic import BaseModel
from datetime import date, datetime


class NotificationOut(BaseModel):
    id: int
    subscription_id: int
    message: str
    notify_date: date
    is_read: bool
    sent_email: bool
    sent_push: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCount(BaseModel):
    count: int