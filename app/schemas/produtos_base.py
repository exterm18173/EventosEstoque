from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProdutoBaseBase(BaseModel):
    nome_base: str = Field(min_length=1, max_length=180)
    categoria_principal_id: Optional[int] = None
    descricao: Optional[str] = None
    ativo: bool = True


class ProdutoBaseCreate(ProdutoBaseBase):
    pass


class ProdutoBaseUpdate(BaseModel):
    nome_base: Optional[str] = Field(default=None, min_length=1, max_length=180)
    categoria_principal_id: Optional[int] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None


class ProdutoBaseRead(ProdutoBaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EstoqueConsolidadoRead(BaseModel):
    produto_base_id: int
    total_quantidade_base: float
    local_id: Optional[int] = None
