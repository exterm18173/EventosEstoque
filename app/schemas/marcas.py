from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarcaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)


class MarcaCreate(MarcaBase):
    pass


class MarcaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=120)


class MarcaRead(MarcaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
