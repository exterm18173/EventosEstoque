from __future__ import annotations

from typing import Optional, List
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class CategoriaProduto(Base, TimestampMixin):
    __tablename__ = "categorias_produto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categorias_produto.id"), nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)

    parent: Mapped[Optional["CategoriaProduto"]] = relationship("CategoriaProduto", remote_side=[id], back_populates="children")
    children: Mapped[List["CategoriaProduto"]] = relationship("CategoriaProduto", back_populates="parent")

    produtos_base_principal: Mapped[List["ProdutoBase"]] = relationship("ProdutoBase", back_populates="categoria_principal")
    produto_tags: Mapped[List["ProdutoCategoria"]] = relationship("ProdutoCategoria", back_populates="categoria")
