from typing import Optional
from pydantic import BaseModel
from datetime import date


class SubscriptionCreate(BaseModel):
    name: str
    amount: float
    currency: str = "CNY"
    billing_cycle: str  # monthly, quarterly, yearly
    first_payment_date: date
    category_id: Optional[int] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    expiry_date: Optional[date] = None
    notify: bool = True


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    billing_cycle: Optional[str] = None
    first_payment_date: Optional[date] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    expiry_date: Optional[date] = None
    notify: Optional[bool] = None
    is_active: Optional[bool] = None


class SubscriptionOut(BaseModel):
    id: int
    name: str
    amount: float
    currency: str
    billing_cycle: str
    first_payment_date: date
    next_payment_date: date
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    expiry_date: Optional[date] = None
    remaining_days: Optional[int] = None
    notify: bool
    is_active: bool

    model_config = {"from_attributes": True}