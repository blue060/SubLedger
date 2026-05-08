from pydantic import BaseModel
from typing import Optional


class MonthlyComparison(BaseModel):
    current_month: float
    last_month: float
    change: float
    currency: str


class CategoryTrendItem(BaseModel):
    month: str
    categories: dict[str, float]


class TopSubscription(BaseModel):
    id: int
    name: str
    amount: float
    currency: str
    converted_amount: float
    category_name: Optional[str] = None
    category_color: Optional[str] = None


class CurrencyBreakdownItem(BaseModel):
    currency: str
    count: int
    total_amount: float
    converted_amount: float