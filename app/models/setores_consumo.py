from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SetorConsumo(Base):
    __tablename__ = "setores_consumo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    movimentacoes: Mapped[list["Movimentacao"]] = relationship(
        "Movimentacao",
        back_populates="setor_consumo",
    )