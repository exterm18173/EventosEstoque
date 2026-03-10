from __future__ import annotations

from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ========= INPUTS (modelo) =========
class SubItemModeloMaoDeObra(BaseModel):
    nome: str
    quantidade: int = Field(default=0, ge=0)

    valor_unitario: Optional[Decimal] = Field(default=None, ge=0)
    valor_total: Optional[Decimal] = Field(default=None, ge=0)

    categoria: Optional[str] = None
    observacao: Optional[str] = None


class GrupoModeloMaoDeObra(BaseModel):
    nome_grupo: str
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None
    subitens: List[SubItemModeloMaoDeObra] = Field(default_factory=list)


class MaoDeObraModeloCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None
    lista_de_grupos: List[GrupoModeloMaoDeObra] = Field(default_factory=list)


class MaoDeObraModeloReplace(BaseModel):
    # para PUT (replace total)
    nome: str = Field(min_length=2, max_length=160)
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None
    lista_de_grupos: List[GrupoModeloMaoDeObra] = Field(default_factory=list)


class MaoDeObraModeloFromEventoInput(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None


# ========= APPLY (aplicar no evento) =========
class AplicarModeloOverride(BaseModel):
    item_modelo_id: int
    quantidade: int = Field(ge=0)


class AplicarModeloPayload(BaseModel):
    # "append" (padrão) ou "replace"
    mode: str = Field(default="append")
    overrides: List[AplicarModeloOverride] = Field(default_factory=list)


# ========= READS =========
class MaoDeObraModeloItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria: Optional[str]
    nome: str
    quantidade: int
    valor_unitario: Optional[Decimal]
    valor_total: Optional[Decimal]
    observacao: Optional[str]


class MaoDeObraModeloGrupoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    modelo_id: int
    nome_grupo: str
    tipo_evento: Optional[str]
    observacao: Optional[str]
    itens: List[MaoDeObraModeloItemRead] = Field(default_factory=list)


class MaoDeObraModeloRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo_evento: Optional[str]
    observacao: Optional[str]
    grupos: List[MaoDeObraModeloGrupoRead] = Field(default_factory=list)


class MaoDeObraModeloListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo_evento: Optional[str]
    observacao: Optional[str]
