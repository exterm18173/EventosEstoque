from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class FornecedorProdutoVinculo(Base, TimestampMixin):
    __tablename__ = "fornecedor_produto_vinculos"
    __table_args__ = (
        UniqueConstraint(
            "fornecedor_cnpj",
            "codigo_fornecedor",
            name="uq_fornecedor_produto_vinculo_codigo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    fornecedor_cnpj: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    codigo_fornecedor: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    descricao_fornecedor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False,
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
    confianca: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    produto: Mapped["Produto"] = relationship("Produto")
    embalagem: Mapped[Optional["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem")
    unidade_informada: Mapped[Optional["Unidade"]] = relationship("Unidade")