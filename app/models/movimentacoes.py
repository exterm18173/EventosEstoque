from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    evento_id: Mapped[Optional[int]] = mapped_column(ForeignKey("eventos.id"), nullable=True, index=True)
    aluguel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alugueis.id"), nullable=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)

    tipo: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # entrada|saida|transferencia|ajuste|perda|devolucao

    quantidade_informada: Mapped[float] = mapped_column(Float, nullable=False)
    unidade_informada_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False, index=True)

    fator_para_base: Mapped[float] = mapped_column(Float, nullable=False)
    quantidade_base: Mapped[float] = mapped_column(Float, nullable=False)

    custo_unitario: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    local_origem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("locais.id"), nullable=True, index=True)
    local_destino_id: Mapped[Optional[int]] = mapped_column(ForeignKey("locais.id"), nullable=True, index=True)

    lote_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lotes.id"), nullable=True, index=True)
    embalagem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("produto_embalagens.id"), nullable=True, index=True)

    barcode_lido: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    origem: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # compra|uso_evento|aluguel|inventario|xml
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    produto: Mapped["Produto"] = relationship("Produto", back_populates="movimentacoes")
    evento: Mapped[Optional["Evento"]] = relationship("Evento", back_populates="movimentacoes")
    aluguel: Mapped[Optional["Aluguel"]] = relationship("Aluguel", back_populates="movimentacoes")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="movimentacoes")

    lote: Mapped[Optional["Lote"]] = relationship("Lote", back_populates="movimentacoes")
    embalagem: Mapped[Optional["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem")
    unidade_informada: Mapped["Unidade"] = relationship("Unidade")
