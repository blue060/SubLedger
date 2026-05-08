from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class PaymentCreate(BaseModel):
    subscription_id: int
    amount: float = Field(ge=0)
    currency: str = "CNY"
    payment_date: date
    status: str = "pending"
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    payment_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    subscription_id: int
    subscription_name: Optional[str] = None
    amount: float
    currency: str
    payment_date: date
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
