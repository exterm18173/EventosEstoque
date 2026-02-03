from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class DespesaBase(BaseModel):
    data: date
    descricao: str = Field(min_length=1, max_length=255)
    valor: float = Field(gt=0)

    categoria: Optional[str] = Field(default=None, max_length=80)  # ex: combustível, alimentação, manutenção
    forma_pagamento: Optional[str] = Field(default=None, max_length=40)  # pix, dinheiro, cartão etc.

    fornecedor_nome: Optional[str] = Field(default=None, max_length=180)
    documento_ref: Optional[str] = Field(default=None, max_length=80)  # nf, recibo, etc

    evento_id: Optional[int] = None
    observacao: Optional[str] = None


class DespesaCreate(DespesaBase):
    pass


class DespesaUpdate(BaseModel):
    data: Optional[date] = None
    descricao: Optional[str] = Field(default=None, min_length=1, max_length=255)
    valor: Optional[float] = Field(default=None, gt=0)

    categoria: Optional[str] = Field(default=None, max_length=80)
    forma_pagamento: Optional[str] = Field(default=None, max_length=40)

    fornecedor_nome: Optional[str] = Field(default=None, max_length=180)
    documento_ref: Optional[str] = Field(default=None, max_length=80)

    evento_id: Optional[int] = None
    observacao: Optional[str] = None


class DespesaRead(DespesaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DespesaImportResult(BaseModel):
    linhas_recebidas: int
    linhas_importadas: int
    linhas_ignoradas: int
    erros: list[str] = []
