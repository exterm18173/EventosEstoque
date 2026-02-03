from __future__ import annotations

from typing import Optional, List
from sqlalchemy import Integer, String, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class ProdutoEmbalagem(Base, TimestampMixin):
    __tablename__ = "produto_embalagens"
    __table_args__ = (
        UniqueConstraint("produto_id", "nome", name="uq_produto_embalagem_nome"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)

    nome: Mapped[str] = mapped_column(String(40), nullable=False)  # unidade|caixa|fardo|pacote
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False, index=True)

    fator_para_base: Mapped[float] = mapped_column(Float, nullable=False)  # ex: 12, 24, 100
    permite_fracionar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    principal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    produto: Mapped["Produto"] = relationship("Produto", back_populates="embalagens")
    unidade: Mapped["Unidade"] = relationship("Unidade", back_populates="embalagens")
    codigos: Mapped[List["ProdutoCodigoBarras"]] = relationship("ProdutoCodigoBarras", back_populates="embalagem", cascade="all, delete-orphan")
