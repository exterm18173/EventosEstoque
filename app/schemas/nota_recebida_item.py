from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotaRecebidaItemBase(BaseModel):
    numero_item: int = Field(gt=0)

    codigo_fornecedor: Optional[str] = Field(default=None, max_length=80)
    codigo_barras: Optional[str] = Field(default=None, max_length=64)

    descricao: str = Field(min_length=1, max_length=255)
    ncm: Optional[str] = Field(default=None, max_length=20)
    cfop: Optional[str] = Field(default=None, max_length=10)

    unidade_comercial: Optional[str] = Field(default=None, max_length=20)
    quantidade: float = Field(gt=0)
    valor_unitario: Optional[float] = Field(default=None, ge=0)
    valor_total: Optional[float] = Field(default=None, ge=0)

    produto_id: Optional[int] = Field(default=None, gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: Optional[int] = Field(default=None, gt=0)
    lote_id: Optional[int] = Field(default=None, gt=0)

    status_conciliacao: str = Field(default="nao_analisado", max_length=30)
    observacao: Optional[str] = None


class NotaRecebidaItemCreate(NotaRecebidaItemBase):
    pass


class NotaRecebidaItemRead(NotaRecebidaItemBase):
    id: int
    nota_recebida_id: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotaRecebidaItemResumo(BaseModel):
    id: int
    numero_item: int
    codigo_fornecedor: Optional[str] = None
    codigo_barras: Optional[str] = None
    descricao: str
    unidade_comercial: Optional[str] = None
    quantidade: float
    valor_unitario: Optional[float] = None
    valor_total: Optional[float] = None
    produto_id: Optional[int] = None
    embalagem_id: Optional[int] = None
    unidade_informada_id: Optional[int] = None
    lote_id: Optional[int] = None
    status_conciliacao: str
    observacao: Optional[str] = None

    class Config:
        from_attributes = True