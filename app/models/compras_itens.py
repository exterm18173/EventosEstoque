from __future__ import annotations

from typing import Optional
from sqlalchemy import Integer, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class CompraItem(Base):
    __tablename__ = "compras_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)

    embalagem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("produto_embalagens.id"), nullable=True, index=True)
    unidade_informada_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False, index=True)

    quantidade_informada: Mapped[float] = mapped_column(Float, nullable=False)
    fator_para_base: Mapped[float] = mapped_column(Float, nullable=False)
    quantidade_base: Mapped[float] = mapped_column(Float, nullable=False)

    valor_unitario_informado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    lote_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lotes.id"), nullable=True, index=True)
    barcode_lido: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    compra: Mapped["Compra"] = relationship("Compra", back_populates="itens")
    produto: Mapped["Produto"] = relationship("Produto")
    embalagem: Mapped[Optional["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem")
    unidade_informada: Mapped["Unidade"] = relationship("Unidade")
    lote: Mapped[Optional["Lote"]] = relationship("Lote")
