from __future__ import annotations

from typing import Optional, List
from sqlalchemy import Integer, String, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class MaoDeObraModelo(Base, TimestampMixin):
    __tablename__ = "mao_de_obra_modelos"
    __table_args__ = (
        # agora o nome é único globalmente (sem user_id)
        UniqueConstraint("nome", name="uq_mdo_modelo_nome"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    nome: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    tipo_evento: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    grupos: Mapped[List["MaoDeObraModeloGrupo"]] = relationship(
        "MaoDeObraModeloGrupo",
        back_populates="modelo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MaoDeObraModeloGrupo(Base, TimestampMixin):
    __tablename__ = "mao_de_obra_modelo_grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("mao_de_obra_modelos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nome_grupo: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    tipo_evento: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    modelo: Mapped["MaoDeObraModelo"] = relationship("MaoDeObraModelo", back_populates="grupos")

    itens: Mapped[List["MaoDeObraModeloItem"]] = relationship(
        "MaoDeObraModeloItem",
        back_populates="grupo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MaoDeObraModeloItem(Base, TimestampMixin):
    __tablename__ = "mao_de_obra_modelo_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("mao_de_obra_modelo_grupos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    categoria: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)

    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    valor_unitario: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    valor_total: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    grupo: Mapped["MaoDeObraModeloGrupo"] = relationship("MaoDeObraModeloGrupo", back_populates="itens")
