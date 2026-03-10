from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class CertificadoFiscal(Base, TimestampMixin):
    __tablename__ = "certificados_fiscais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    empresa_nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(String(20), nullable=False, index=True, unique=True)

    ambiente: Mapped[str] = mapped_column(String(20), nullable=False, default="producao", index=True)
    tipo_certificado: Mapped[str] = mapped_column(String(20), nullable=False, default="A1")

    arquivo_path: Mapped[str] = mapped_column(Text, nullable=False)
    senha_criptografada: Mapped[str] = mapped_column(Text, nullable=False)

    data_validade: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    ultimo_nsu: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    ultima_sincronizacao: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sincronizacao_automatica: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    notas_recebidas: Mapped[List["NotaRecebida"]] = relationship(
        "NotaRecebida",
        back_populates="certificado_fiscal",
        cascade="all, delete-orphan",
    )