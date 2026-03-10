from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UsuarioBase(BaseModel):
    nome: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=200)
    perfil: str = Field(default="admin", min_length=1, max_length=40)
    ativo: bool = Field(default=True)


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=160)
    email: Optional[str] = Field(default=None, min_length=3, max_length=200)
    perfil: Optional[str] = Field(default=None, min_length=1, max_length=40)
    ativo: Optional[bool] = None


class UsuarioRead(UsuarioBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
