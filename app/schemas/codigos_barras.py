from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CodigoBarrasBase(BaseModel):
    embalagem_id: int
    codigo: str = Field(min_length=1, max_length=64)
    tipo: str = Field(min_length=1, max_length=20)  # ean13|ean8|code128|interno
    principal: bool = False
    ativo: bool = True


class CodigoBarrasCreate(CodigoBarrasBase):
    pass


class CodigoBarrasUpdate(BaseModel):
    embalagem_id: Optional[int] = None
    codigo: Optional[str] = Field(default=None, min_length=1, max_length=64)
    tipo: Optional[str] = Field(default=None, min_length=1, max_length=20)
    principal: Optional[bool] = None
    ativo: Optional[bool] = None


class CodigoBarrasRead(CodigoBarrasBase):
    id: int
    produto_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BarcodeLookupResponse(BaseModel):
    codigo: str
    produto_id: int
    embalagem_id: int
    fator_para_base: float
    unidade_base_id: int
    nome_produto: str
    nome_embalagem: str
    ativo: bool
    principal: bool
