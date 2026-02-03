from __future__ import annotations

from datetime import date
from typing import Optional, List
from sqlalchemy import Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Evento(Base, TimestampMixin):
    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)

    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(40), default="ativo", nullable=False, index=True)
    local_evento: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="eventos")
    movimentacoes: Mapped[List["Movimentacao"]] = relationship("Movimentacao", back_populates="evento")
    alugueis: Mapped[List["Aluguel"]] = relationship("Aluguel", back_populates="evento")
