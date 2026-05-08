from pydantic import BaseModel
from typing import Optional


class AdvisorTip(BaseModel):
    type: str  # price_increase, duplicate_service, near_expiry, cancel_to_save
    subscription_id: int
    subscription_name: str
    message: str
    savings: Optional[float] = None
    currency: Optional[str] = None