from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClienteBase(BaseModel):
    nome: str = Field(min_length=1, max_length=160)
    documento: Optional[str] = Field(default=None, max_length=30)  # CPF/CNPJ (MVP sem validação rígida)
    telefone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=120)


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=160)
    documento: Optional[str] = Field(default=None, max_length=30)
    telefone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=120)


class ClienteRead(ClienteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
