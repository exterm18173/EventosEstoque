from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProdutoBaseSchema(BaseModel):
    produto_base_id: int
    marca_id: Optional[int] = None
    nome_comercial: str = Field(min_length=1, max_length=220)
    unidade_base_id: int

    sku: Optional[str] = Field(default=None, max_length=80)
    ativo: bool = True

    eh_alugavel: bool = False
    controla_lote: bool = False
    controla_validade: bool = False

    estoque_minimo: Optional[float] = None
    custo_medio: Optional[float] = None
    preco_reposicao: Optional[float] = None


class ProdutoCreate(ProdutoBaseSchema):
    pass


class ProdutoUpdate(BaseModel):
    produto_base_id: Optional[int] = None
    marca_id: Optional[int] = None
    nome_comercial: Optional[str] = Field(default=None, min_length=1, max_length=220)
    unidade_base_id: Optional[int] = None

    sku: Optional[str] = Field(default=None, max_length=80)
    ativo: Optional[bool] = None

    eh_alugavel: Optional[bool] = None
    controla_lote: Optional[bool] = None
    controla_validade: Optional[bool] = None

    estoque_minimo: Optional[float] = None
    custo_medio: Optional[float] = None
    preco_reposicao: Optional[float] = None


class ProdutoRead(ProdutoBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProdutoListItem(BaseModel):
    id: int
    produto_base_id: int
    marca_id: Optional[int] = None
    nome_comercial: str
    unidade_base_id: int
    sku: Optional[str] = None
    ativo: bool
    eh_alugavel: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
