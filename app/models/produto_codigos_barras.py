from __future__ import annotations

from sqlalchemy import Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class ProdutoCodigoBarras(Base, TimestampMixin):
    __tablename__ = "produto_codigos_barras"
    __table_args__ = (UniqueConstraint("codigo", name="uq_barcode_codigo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    embalagem_id: Mapped[int] = mapped_column(ForeignKey("produto_embalagens.id"), nullable=False, index=True)

    codigo: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # ean13|ean8|code128|interno
    principal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    produto: Mapped["Produto"] = relationship("Produto", back_populates="codigos_barras")
    embalagem: Mapped["ProdutoEmbalagem"] = relationship("ProdutoEmbalagem", back_populates="codigos")
