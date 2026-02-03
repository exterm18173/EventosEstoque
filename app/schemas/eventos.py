from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class EventoBase(BaseModel):
    cliente_id: int
    nome: str = Field(min_length=1, max_length=180)
    data_inicio: date
    data_fim: Optional[date] = None
    status: str = Field(default="planejado", max_length=30)  # planejado|confirmado|em_execucao|finalizado|cancelado
    local_evento: Optional[str] = Field(default=None, max_length=200)
    observacao: Optional[str] = None


class EventoCreate(EventoBase):
    pass


class EventoUpdate(BaseModel):
    cliente_id: Optional[int] = None
    nome: Optional[str] = Field(default=None, min_length=1, max_length=180)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    status: Optional[str] = Field(default=None, max_length=30)
    local_evento: Optional[str] = Field(default=None, max_length=200)
    observacao: Optional[str] = None


class EventoRead(EventoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
