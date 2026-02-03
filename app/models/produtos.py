from __future__ import annotations

from typing import Optional, List
from sqlalchemy import Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Produto(Base, TimestampMixin):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_base_id: Mapped[int] = mapped_column(ForeignKey("produtos_base.id"), nullable=False, index=True)
    marca_id: Mapped[Optional[int]] = mapped_column(ForeignKey("marcas.id"), nullable=True, index=True)

    nome_comercial: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    unidade_base_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False, index=True)

    sku: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    eh_alugavel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    controla_lote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    controla_validade: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    estoque_minimo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    custo_medio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preco_reposicao: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    produto_base: Mapped["ProdutoBase"] = relationship("ProdutoBase", back_populates="variacoes")
    marca: Mapped[Optional["Marca"]] = relationship("Marca", back_populates="produtos")
    unidade_base: Mapped["Unidade"] = relationship("Unidade", back_populates="produtos_base")

    tags: Mapped[List["ProdutoCategoria"]] = relationship("ProdutoCategoria", back_populates="produto", cascade="all, delete-orphan")
    embalagens: Mapped[List["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem", back_populates="produto", cascade="all, delete-orphan")
    codigos_barras: Mapped[List["ProdutoCodigoBarras"]] = relationship("ProdutoCodigoBarras", back_populates="produto", cascade="all, delete-orphan")

    saldos: Mapped[List["EstoqueSaldo"]] = relationship("EstoqueSaldo", back_populates="produto")
    lotes: Mapped[List["Lote"]] = relationship("Lote", back_populates="produto")
    movimentacoes: Mapped[List["Movimentacao"]] = relationship("Movimentacao", back_populates="produto")
    aluguel_itens: Mapped[List["AluguelItem"]] = relationship("AluguelItem", back_populates="produto")
