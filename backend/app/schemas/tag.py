from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TagCreate(BaseModel):
    name: str = Field(min_length=1)
    color: Optional[str] = None


class TagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    color: Optional[str] = None


class TagOut(BaseModel):
    id: int
    name: str
    color: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
