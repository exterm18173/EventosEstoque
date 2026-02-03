from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UnidadeBase(BaseModel):
    sigla: str = Field(min_length=1, max_length=20)
    descricao: str = Field(min_length=1, max_length=120)


class UnidadeCreate(UnidadeBase):
    pass


class UnidadeUpdate(BaseModel):
    sigla: Optional[str] = Field(default=None, min_length=1, max_length=20)
    descricao: Optional[str] = Field(default=None, min_length=1, max_length=120)


class UnidadeRead(UnidadeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
