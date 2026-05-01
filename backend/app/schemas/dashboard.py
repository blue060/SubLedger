from pydantic import BaseModel
from typing import Optional
from datetime import date


class DashboardSummary(BaseModel):
    monthly_total: float
    monthly_total_currency: str
    next_month_projected: float
    next_month_projected_currency: str


class CategoryStat(BaseModel):
    category_name: str
    color: Optional[str] = None
    total_amount: float


class CalendarEntry(BaseModel):
    date: date
    subscription_name: str
    amount: float
    currency: str
    converted_amount: float