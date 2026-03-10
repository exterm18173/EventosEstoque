from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class NotaImportacaoLog(Base, TimestampMixin):
    __tablename__ = "notas_importacao_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    nota_recebida_id: Mapped[int] = mapped_column(
        ForeignKey("notas_recebidas.id"),
        nullable=False,
        index=True,
    )

    usuario_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    tipo_evento: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    nota_recebida: Mapped["NotaRecebida"] = relationship(
        "NotaRecebida",
        back_populates="logs",
    )

    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario")