from __future__ import annotations

from typing import Optional, List
from sqlalchemy import Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class ProdutoBase(Base, TimestampMixin):
    __tablename__ = "produtos_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_base: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    categoria_principal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categorias_produto.id"), nullable=True, index=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    categoria_principal: Mapped[Optional["CategoriaProduto"]] = relationship("CategoriaProduto", back_populates="produtos_base_principal")
    variacoes: Mapped[List["Produto"]] = relationship("Produto", back_populates="produto_base")
