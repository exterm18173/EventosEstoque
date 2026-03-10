from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class NotaRecebida(Base, TimestampMixin):
    __tablename__ = "notas_recebidas"
    __table_args__ = (
        UniqueConstraint("chave_acesso", name="uq_notas_recebidas_chave_acesso"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    certificado_fiscal_id: Mapped[int] = mapped_column(
        ForeignKey("certificados_fiscais.id"),
        nullable=False,
        index=True,
    )

    fornecedor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("fornecedores.id"),
        nullable=True,
        index=True,
    )

    compra_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("compras.id"),
        nullable=True,
        index=True,
    )

    chave_acesso: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    serie: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    modelo: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    fornecedor_nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    fornecedor_cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    natureza_operacao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cfop_predominante: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    data_emissao: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    data_autorizacao: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    valor_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_produtos: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_frete: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_desconto: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valor_outros: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    protocolo: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    nsu: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="nova", index=True)

    xml_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    xml_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importada_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    certificado_fiscal: Mapped["CertificadoFiscal"] = relationship(
        "CertificadoFiscal",
        back_populates="notas_recebidas",
    )

    fornecedor: Mapped[Optional["Fornecedor"]] = relationship(
    "Fornecedor",
    back_populates="notas_recebidas",
)
    compra: Mapped[Optional["Compra"]] = relationship("Compra")

    itens: Mapped[List["NotaRecebidaItem"]] = relationship(
        "NotaRecebidaItem",
        back_populates="nota_recebida",
        cascade="all, delete-orphan",
    )

    logs: Mapped[List["NotaImportacaoLog"]] = relationship(
        "NotaImportacaoLog",
        back_populates="nota_recebida",
        cascade="all, delete-orphan",
    )