from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class LoteBase(BaseModel):
    produto_id: int
    local_id: int
    codigo_lote: str = Field(min_length=1, max_length=80)
    validade: Optional[date] = None


class LoteCreate(LoteBase):
    quantidade_base_atual: float = Field(default=0, ge=0)


class LoteUpdate(BaseModel):
    produto_id: Optional[int] = None
    local_id: Optional[int] = None
    codigo_lote: Optional[str] = Field(default=None, min_length=1, max_length=80)
    validade: Optional[date] = None
    quantidade_base_atual: Optional[float] = Field(default=None, ge=0)


class LoteRead(LoteBase):
    id: int
    quantidade_base_atual: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
