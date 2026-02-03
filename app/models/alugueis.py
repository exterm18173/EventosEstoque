from __future__ import annotations

from datetime import date
from typing import Optional, List
from sqlalchemy import Integer, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Aluguel(Base, TimestampMixin):
    __tablename__ = "alugueis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    evento_id: Mapped[Optional[int]] = mapped_column(ForeignKey("eventos.id"), nullable=True, index=True)

    data_saida_prevista: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_devolucao_prevista: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_devolucao_real: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(20), default="rascunho", nullable=False, index=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="alugueis")
    evento: Mapped[Optional["Evento"]] = relationship("Evento", back_populates="alugueis")
    itens: Mapped[List["AluguelItem"]] = relationship("AluguelItem", back_populates="aluguel", cascade="all, delete-orphan")
    movimentacoes: Mapped[List["Movimentacao"]] = relationship("Movimentacao", back_populates="aluguel")
