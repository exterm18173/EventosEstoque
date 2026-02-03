from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import Integer, String, Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class NfeDocumento(Base):
    __tablename__ = "nfe_documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fornecedor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fornecedores.id"), nullable=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)

    chave_acesso: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    numero: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    serie: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    data_emissao: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status_importacao: Mapped[str] = mapped_column(String(20), default="recebida", nullable=False, index=True)  # recebida|processada|erro|duplicada
    xml_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    xml_hash: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    recebida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    fornecedor: Mapped[Optional["Fornecedor"]] = relationship("Fornecedor", back_populates="nfe_documentos")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="nfe_documentos")
    itens: Mapped[List["NfeItem"]] = relationship("NfeItem", back_populates="documento", cascade="all, delete-orphan")
    compra: Mapped[Optional["Compra"]] = relationship("Compra", back_populates="nfe_documento", uselist=False)
