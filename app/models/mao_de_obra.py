from __future__ import annotations

from typing import Optional, List
from sqlalchemy import Integer, String, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class MaoDeObraGrupo(Base, TimestampMixin):
    __tablename__ = "mao_de_obra_grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    evento_id: Mapped[int] = mapped_column(
        ForeignKey("eventos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nome_grupo: Mapped[str] = mapped_column(String(160), nullable=False, index=True)

    # Ex: casamento, formatura, aniversario... (ou “tipoEvento” do seu input)
    tipo_evento: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evento: Mapped["Evento"] = relationship("Evento", back_populates="mao_de_obra_grupos")

    subitens: Mapped[List["MaoDeObraItem"]] = relationship(
        "MaoDeObraItem",
        back_populates="grupo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MaoDeObraItem(Base, TimestampMixin):
    __tablename__ = "mao_de_obra_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("mao_de_obra_grupos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # “categoria” do update (ex: garçom, segurança, limpeza...)
    categoria: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)

    nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)

    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    valor_unitario: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    grupo: Mapped["MaoDeObraGrupo"] = relationship("MaoDeObraGrupo", back_populates="subitens")
