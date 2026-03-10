from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FornecedorProdutoVinculoBase(BaseModel):
    fornecedor_cnpj: str = Field(min_length=11, max_length=20)
    codigo_fornecedor: Optional[str] = Field(default=None, max_length=80)
    descricao_fornecedor: Optional[str] = Field(default=None, max_length=255)

    produto_id: int = Field(gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: Optional[int] = Field(default=None, gt=0)

    fator_para_base: Optional[float] = Field(default=None, gt=0)
    confianca: Optional[float] = Field(default=None, ge=0)


class FornecedorProdutoVinculoCreate(FornecedorProdutoVinculoBase):
    pass


class FornecedorProdutoVinculoUpdate(BaseModel):
    fornecedor_cnpj: Optional[str] = Field(default=None, min_length=11, max_length=20)
    codigo_fornecedor: Optional[str] = Field(default=None, max_length=80)
    descricao_fornecedor: Optional[str] = Field(default=None, max_length=255)

    produto_id: Optional[int] = Field(default=None, gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: Optional[int] = Field(default=None, gt=0)

    fator_para_base: Optional[float] = Field(default=None, gt=0)
    confianca: Optional[float] = Field(default=None, ge=0)


class FornecedorProdutoVinculoRead(FornecedorProdutoVinculoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True