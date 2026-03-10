from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class NotaRecebidaItem(Base, TimestampMixin):
    __tablename__ = "notas_recebidas_itens"
    __table_args__ = (
        UniqueConstraint(
            "nota_recebida_id",
            "numero_item",
            name="uq_notas_recebidas_itens_nota_item",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    nota_recebida_id: Mapped[int] = mapped_column(
        ForeignKey("notas_recebidas.id"),
        nullable=False,
        index=True,
    )

    numero_item: Mapped[int] = mapped_column(Integer, nullable=False)

    codigo_fornecedor: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    codigo_barras: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    descricao: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ncm: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    cfop: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    unidade_comercial: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    valor_unitario: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    produto_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=True,
        index=True,
    )

    embalagem_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("produto_embalagens.id"),
        nullable=True,
        index=True,
    )

    unidade_informada_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("unidades.id"),
        nullable=True,
        index=True,
    )

    lote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lotes.id"),
        nullable=True,
        index=True,
    )

    status_conciliacao: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="nao_analisado",
        index=True,
    )

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    nota_recebida: Mapped["NotaRecebida"] = relationship(
        "NotaRecebida",
        back_populates="itens",
    )

    produto: Mapped[Optional["Produto"]] = relationship("Produto")
    embalagem: Mapped[Optional["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem")
    unidade_informada: Mapped[Optional["Unidade"]] = relationship("Unidade")
    lote: Mapped[Optional["Lote"]] = relationship("Lote")

    conciliacoes: Mapped[List["NotaConciliacaoItem"]] = relationship(
        "NotaConciliacaoItem",
        back_populates="nota_recebida_item",
        cascade="all, delete-orphan",
    )