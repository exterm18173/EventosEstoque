from __future__ import annotations

from typing import Optional
from sqlalchemy import Integer, Float, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class AluguelItem(Base):
    __tablename__ = "aluguel_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluguel_id: Mapped[int] = mapped_column(ForeignKey("alugueis.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)

    quantidade_base: Mapped[float] = mapped_column(Float, nullable=False)
    quantidade_devolvida_base: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    valor_unitario: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status_item: Mapped[str] = mapped_column(String(20), default="ok", nullable=False, index=True)  # ok|danificado|faltando
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    aluguel: Mapped["Aluguel"] = relationship("Aluguel", back_populates="itens")
    produto: Mapped["Produto"] = relationship("Produto", back_populates="aluguel_itens")
