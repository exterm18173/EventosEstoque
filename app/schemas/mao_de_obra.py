# app/schemas/mao_de_obra.py
from __future__ import annotations

from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ========= INPUTS =========
class SubItemMaoDeObra(BaseModel):
    nome: str
    quantidade: int = Field(default=0, ge=0)

    # Dinheiro como Decimal (evita warning do Pylance e evita float)
    valor_unitario: Optional[Decimal] = Field(default=None, ge=0)
    valor_total: Optional[Decimal] = Field(default=None, ge=0)

    categoria: Optional[str] = None
    observacao: Optional[str] = None


class GrupoMaoDeObra(BaseModel):
    nome_grupo: str
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None
    subitens: List[SubItemMaoDeObra] = Field(default_factory=list)


class MaoDeObraInput(BaseModel):
    evento_id: int
    lista_de_grupos: List[GrupoMaoDeObra] = Field(default_factory=list)


# Payload do APPEND (evento_id vem pela rota)
class MaoDeObraAppendInput(BaseModel):
    lista_de_grupos: List[GrupoMaoDeObra] = Field(default_factory=list)


class MaoDeObraItemUpdate(BaseModel):
    categoria: Optional[str] = None
    nome: str
    quantidade: int = Field(ge=0)

    valor_unitario: Optional[Decimal] = Field(default=None, ge=0)
    valor_total: Optional[Decimal] = Field(default=None, ge=0)

    observacao: Optional[str] = None


# ========= READS =========
class MaoDeObraItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria: Optional[str]
    nome: str
    quantidade: int
    valor_unitario: Optional[Decimal]
    valor_total: Optional[Decimal]
    observacao: Optional[str]


class MaoDeObraGrupoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evento_id: int
    nome_grupo: str
    tipo_evento: Optional[str]
    observacao: Optional[str]
    subitens: List[MaoDeObraItemRead] = Field(default_factory=list)


class MaoDeObraResumoRead(BaseModel):
    evento_id: int
    total: float
    por_categoria: List[dict]  # [{"categoria": "...", "total": 123.0}]


class MaoDeObraResponse(BaseModel):
    evento_id: int
    grupos: List[MaoDeObraGrupoRead] = Field(default_factory=list)
    total: float
