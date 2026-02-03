from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LocalBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    tipo: Optional[str] = Field(default=None, max_length=50)  # deposito|cozinha|caminhao|evento|outro
    descricao: Optional[str] = Field(default=None, max_length=255)


class LocalCreate(LocalBase):
    pass


class LocalUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=120)
    tipo: Optional[str] = Field(default=None, max_length=50)
    descricao: Optional[str] = Field(default=None, max_length=255)


class LocalRead(LocalBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
