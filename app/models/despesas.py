from __future__ import annotations

from typing import Optional
from datetime import date

from sqlalchemy import Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Despesa(Base, TimestampMixin):
    __tablename__ = "despesas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)

    valor: Mapped[float] = mapped_column(Float, nullable=False)

    categoria: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    forma_pagamento: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    fornecedor_nome: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    documento_ref: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    evento_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("eventos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # relationships
    evento: Mapped[Optional["Evento"]] = relationship("Evento", lazy="selectin")
