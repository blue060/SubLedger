from pydantic import BaseModel
from datetime import datetime


class PriceHistoryOut(BaseModel):
    id: int
    old_amount: float
    new_amount: float
    old_currency: str
    new_currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
