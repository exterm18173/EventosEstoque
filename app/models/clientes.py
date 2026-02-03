from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Cliente(Base, TimestampMixin):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    documento: Mapped[str] = mapped_column(String(40), nullable=True, index=True)
    telefone: Mapped[str] = mapped_column(String(40), nullable=True)
    email: Mapped[str] = mapped_column(String(160), nullable=True)

    eventos = relationship("Evento", back_populates="cliente")
    alugueis = relationship("Aluguel", back_populates="cliente")
