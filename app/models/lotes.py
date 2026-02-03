from __future__ import annotations

from datetime import date
from typing import Optional, List
from sqlalchemy import Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Lote(Base, TimestampMixin):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    codigo_lote: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    validade: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    quantidade_base_atual: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    local_id: Mapped[int] = mapped_column(ForeignKey("locais.id"), nullable=False, index=True)

    produto: Mapped["Produto"] = relationship("Produto", back_populates="lotes")
    local: Mapped["Local"] = relationship("Local", back_populates="lotes")
    movimentacoes: Mapped[List["Movimentacao"]] = relationship("Movimentacao", back_populates="lote")
