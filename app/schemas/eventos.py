from __future__ import annotations

from datetime import datetime, date
from typing import Optional, Literal, List
from typing_extensions import Annotated

from pydantic import BaseModel, Field, condecimal, ConfigDict

Money = Annotated[condecimal(max_digits=14, decimal_places=2), Field(default=None)]


class EventoPrincipalCreate(BaseModel):
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


class SubeventoCreate(BaseModel):
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


class EventoUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=200)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

    status: Optional[str] = Field(default=None, max_length=40)
    local_evento: Optional[str] = Field(default=None, max_length=200)
    observacao: Optional[str] = None

    receita: Optional[Money] = None
    receita_convite_extra: Optional[Money] = None


class EventoResumoPai(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    data_inicio: date
    data_fim: date
    status: str
    tipo_evento: Literal["principal", "subevento"]


class EventoResumoFilho(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    data_inicio: date
    data_fim: date
    status: str
    tipo_evento: Literal["principal", "subevento"]
    receita: Optional[Money] = None
    receita_convite_extra: Optional[Money] = None


class EventoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    nome: str

    data_inicio: date
    data_fim: date

    status: str
    local_evento: Optional[str] = None
    observacao: Optional[str] = None

    receita: Optional[Money] = None
    receita_convite_extra: Optional[Money] = None

    tipo_evento: Literal["principal", "subevento"]
    evento_pai_id: Optional[int] = None
    total_subeventos: int = 0

    created_at: datetime
    updated_at: datetime


class EventoDetalheRead(EventoRead):
    evento_pai: Optional[EventoResumoPai] = None
    subeventos: List[EventoResumoFilho] = Field(default_factory=list)