from __future__ import annotations

from typing import Optional
from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class NfeItem(Base):
    __tablename__ = "nfe_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfe_documento_id: Mapped[int] = mapped_column(ForeignKey("nfe_documentos.id"), nullable=False, index=True)

    descricao_xml: Mapped[str] = mapped_column(String(300), nullable=False)
    ean_xml: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    ncm: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    unidade_xml_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False, index=True)
    quantidade_xml: Mapped[float] = mapped_column(Float, nullable=False)
    valor_unitario_xml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_total_xml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    produto_id_sugerido: Mapped[Optional[int]] = mapped_column(ForeignKey("produtos.id"), nullable=True, index=True)
    embalagem_id_sugerida: Mapped[Optional[int]] = mapped_column(ForeignKey("produto_embalagens.id"), nullable=True, index=True)
    fator_sugerido: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pendente", nullable=False, index=True)  # pendente|vinculado|ignorado

    documento: Mapped["NfeDocumento"] = relationship("NfeDocumento", back_populates="itens")
    unidade_xml: Mapped["Unidade"] = relationship("Unidade")
    produto_sugerido: Mapped[Optional["Produto"]] = relationship("Produto")
    embalagem_sugerida: Mapped[Optional["ProdutoEmbalagem"]] = relationship("ProdutoEmbalagem")
