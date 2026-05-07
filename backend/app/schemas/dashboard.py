from pydantic import BaseModel
from typing import Optional
from datetime import date


class DashboardSummary(BaseModel):
    monthly_total: float
    monthly_total_currency: str
    next_month_projected: float
    next_month_projected_currency: str
    yearly_total: float = 0
    yearly_total_currency: str = "CNY"
    last_month_total: float = 0
    last_month_total_currency: str = "CNY"
    monthly_change: float = 0


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
    category_color: Optional[str] = None


class ExpiringSubscription(BaseModel):
    id: int
    name: str
    expiry_date: date
    remaining_days: int


class MonthlyTrend(BaseModel):
    month: str
    total: float


class BudgetStatus(BaseModel):
    budget: Optional[float] = None
    spent: float
    remaining: Optional[float] = None
    exceeded: bool = False