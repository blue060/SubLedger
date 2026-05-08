from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BackupOut(BaseModel):
    id: int
    file_path: str
    file_size: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
