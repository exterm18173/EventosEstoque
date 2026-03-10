from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class NotaConciliacaoItem(Base, TimestampMixin):
    __tablename__ = "notas_conciliacoes_itens"
    __table_args__ = (
        UniqueConstraint(
            "nota_recebida_item_id",
            name="uq_notas_conciliacoes_itens_item",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    nota_recebida_item_id: Mapped[int] = mapped_column(
        ForeignKey("notas_recebidas_itens.id"),
        nullable=False,
        index=True,
    )

    acao: Mapped[str] = mapped_column(String(30), nullable=False, default="pendente", index=True)
    # pendente | vincular_existente | criar_produto | ignorar | conflito

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

    fator_para_base: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    barcode_final: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    lote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lotes.id"),
        nullable=True,
        index=True,
    )

    criar_produto_novo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nome_produto_sugerido: Mapped[Optional[str]] = mapped_column(String(220), nullable=True)

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    nota_recebida_item: Mapped["NotaRecebidaItem"] = relationship(
        "NotaRecebidaItem",
        back_populates="conciliacoes",
    )

    produto: Mapped[Optional["Produto"]] = relationship("Produto")
    embalagem: Mapped[Optional["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem")
    unidade_informada: Mapped[Optional["Unidade"]] = relationship("Unidade")
    lote: Mapped[Optional["Lote"]] = relationship("Lote")