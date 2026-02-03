from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FornecedorBase(BaseModel):
    nome: str = Field(min_length=1, max_length=180)
    documento: Optional[str] = Field(default=None, max_length=30)  # CNPJ/CPF (MVP)
    telefone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=120)


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=180)
    documento: Optional[str] = Field(default=None, max_length=30)
    telefone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=120)


class FornecedorRead(FornecedorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
