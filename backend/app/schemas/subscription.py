from typing import Optional
from pydantic import BaseModel, model_validator
from datetime import date


class SubscriptionCreate(BaseModel):
    name: str
    amount: float
    currency: str = "CNY"
    billing_cycle: str  # monthly, quarterly, yearly, once, custom
    billing_cycle_num: int = 1  # for custom: e.g. 2 for "every 2 years"
    billing_cycle_unit: str = "month"  # month or year, for custom
    first_payment_date: date
    category_id: Optional[int] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    expiry_date: Optional[date] = None
    payment_method: Optional[str] = None
    intro_amount: Optional[float] = None
    intro_months: Optional[int] = None
    notify: bool = True

    @model_validator(mode="after")
    def validate_billing_cycle_fields(self):
        if self.billing_cycle == "custom":
            if not self.billing_cycle_num or not self.billing_cycle_unit:
                raise ValueError("自定义周期需要填写周期数和周期单位")
        if self.intro_amount is not None and self.intro_months is None:
            raise ValueError("设置优惠价格时需同时填写优惠月数")
        if self.intro_months is not None and self.intro_amount is None:
            raise ValueError("设置优惠月数时需同时填写优惠价格")
        return self


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    billing_cycle: Optional[str] = None
    billing_cycle_num: Optional[int] = None
    billing_cycle_unit: Optional[str] = None
    first_payment_date: Optional[date] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    expiry_date: Optional[date] = None
    payment_method: Optional[str] = None
    intro_amount: Optional[float] = None
    intro_months: Optional[int] = None
    notify: Optional[bool] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_billing_cycle_fields(self):
        if self.billing_cycle == "custom":
            if not self.billing_cycle_num or not self.billing_cycle_unit:
                raise ValueError("自定义周期需要填写周期数和周期单位")
        if self.intro_amount is not None and self.intro_months is None:
            raise ValueError("设置优惠价格时需同时填写优惠月数")
        if self.intro_months is not None and self.intro_amount is None:
            raise ValueError("设置优惠月数时需同时填写优惠价格")
        return self


class SubscriptionOut(BaseModel):
    id: int
    name: str
    amount: float
    currency: str
    billing_cycle: str
    billing_cycle_num: int = 1
    billing_cycle_unit: str = "month"
    first_payment_date: date
    next_payment_date: Optional[date] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    expiry_date: Optional[date] = None
    payment_method: Optional[str] = None
    intro_amount: Optional[float] = None
    intro_months: Optional[int] = None
    remaining_days: Optional[int] = None
    notify: bool
    is_active: bool

    model_config = {"from_attributes": True}