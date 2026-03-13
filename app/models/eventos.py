from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import Integer, String, Date, ForeignKey, Text, Numeric, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property, aliased

from .base import Base, TimestampMixin


class Evento(Base, TimestampMixin):
    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=False,
        index=True,
    )

    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(40),
        default="planejado",
        nullable=False,
        index=True,
    )

    local_evento: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    receita: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    receita_convite_extra: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    tipo_evento: Mapped[str] = mapped_column(
        String(20),
        default="principal",
        nullable=False,
        index=True,
    )

    evento_pai_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("eventos.id"),
        nullable=True,
        index=True,
    )

    cliente: Mapped["Cliente"] = relationship(
        "Cliente",
        back_populates="eventos",
    )

    movimentacoes: Mapped[List["Movimentacao"]] = relationship(
        "Movimentacao",
        back_populates="evento",
    )

    alugueis: Mapped[List["Aluguel"]] = relationship(
        "Aluguel",
        back_populates="evento",
    )

    mao_de_obra_grupos: Mapped[List["MaoDeObraGrupo"]] = relationship(
        "MaoDeObraGrupo",
        back_populates="evento",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    evento_pai: Mapped[Optional["Evento"]] = relationship(
        "Evento",
        remote_side="Evento.id",
        back_populates="subeventos",
    )

    subeventos: Mapped[List["Evento"]] = relationship(
        "Evento",
        back_populates="evento_pai",
        lazy="selectin",
    )

    @classmethod
    def __declare_last__(cls) -> None:
        # evita disparar configuração precoce dos mappers
        if "total_subeventos" not in cls.__dict__:
            evento_filho = aliased(cls)
            cls.total_subeventos = column_property(
                select(func.count(evento_filho.id))
                .where(evento_filho.evento_pai_id == cls.id)
                .correlate_except(evento_filho)
                .scalar_subquery()
            )