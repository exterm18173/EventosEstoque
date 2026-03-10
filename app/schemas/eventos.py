from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from typing_extensions import Annotated

from pydantic import BaseModel, Field, condecimal

Money = Annotated[condecimal(max_digits=14, decimal_places=2), Field(default=None)]
# ^ aqui Money vira um "tipo" de verdade pro type checker

class EventoBase(BaseModel):
    cliente_id: int
    nome: str = Field(min_length=1, max_length=200)

    data_inicio: date
    data_fim: Optional[date] = None

    status: str = Field(
        default="planejado",
        max_length=40,
        description="planejado|confirmado|em_execucao|finalizado|cancelado",
    )

    local_evento: Optional[str] = Field(default=None, max_length=200)
    observacao: Optional[str] = None

    receita: Optional[Money] = None
    receita_convite_extra: Optional[Money] = None


class EventoCreate(EventoBase):
    pass


class EventoUpdate(BaseModel):
    cliente_id: Optional[int] = None
    nome: Optional[str] = Field(default=None, min_length=1, max_length=200)

    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

    status: Optional[str] = Field(default=None, max_length=40)
    local_evento: Optional[str] = Field(default=None, max_length=200)
    observacao: Optional[str] = None

    receita: Optional[Money] = None
    receita_convite_extra: Optional[Money] = None


class EventoRead(EventoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
