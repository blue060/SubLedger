from typing import Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
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