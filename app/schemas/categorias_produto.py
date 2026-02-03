from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class CategoriaProdutoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    tipo: Optional[str] = Field(default=None, max_length=60)
    parent_id: Optional[int] = None


class CategoriaProdutoCreate(CategoriaProdutoBase):
    pass


class CategoriaProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=120)
    tipo: Optional[str] = Field(default=None, max_length=60)
    parent_id: Optional[int] = None


class CategoriaProdutoRead(CategoriaProdutoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoriaProdutoTreeNode(BaseModel):
    id: int
    nome: str
    tipo: Optional[str] = None
    parent_id: Optional[int] = None
    children: List["CategoriaProdutoTreeNode"] = []

    class Config:
        from_attributes = True


CategoriaProdutoTreeNode.model_rebuild()
