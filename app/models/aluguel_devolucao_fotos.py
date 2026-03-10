# app/models/aluguel_devolucao_fotos.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import Integer, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class AluguelDevolucaoFoto(Base, TimestampMixin):
    __tablename__ = "aluguel_devolucao_fotos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluguel_item_id: Mapped[int] = mapped_column(ForeignKey("aluguel_itens.id"), index=True, nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True, nullable=False)
    movimentacao_id: Mapped[Optional[int]] = mapped_column(ForeignKey("movimentacoes.id"), index=True, nullable=True)

    path: Mapped[str] = mapped_column(Text, nullable=False)
    mime: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    nome_original: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    item: Mapped["AluguelItem"] = relationship("AluguelItem")
