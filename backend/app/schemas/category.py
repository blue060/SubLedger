from typing import Optional
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}