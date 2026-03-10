from __future__ import annotations

from datetime import date
from typing import Optional, List
from sqlalchemy import Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Compra(Base, TimestampMixin):
    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    nfe_documento_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nfe_documentos.id"), nullable=True, index=True)

    numero_documento: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    data_compra: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="aberta", nullable=False, index=True)

    fornecedor: Mapped["Fornecedor"] = relationship("Fornecedor", back_populates="compras")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="compras")
    nfe_documento: Mapped[Optional["NfeDocumento"]] = relationship("NfeDocumento", back_populates="compra")

    itens: Mapped[List["CompraItem"]] = relationship(
        "CompraItem",
        back_populates="compra",
        cascade="all, delete-orphan",
    )

    notas_recebidas: Mapped[List["NotaRecebida"]] = relationship("NotaRecebida", back_populates="compra")