from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Local(Base, TimestampMixin):
    __tablename__ = "locais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # deposito|caminhao|salao
    descricao: Mapped[str] = mapped_column(Text, nullable=True)

    saldos = relationship("EstoqueSaldo", back_populates="local")
    lotes = relationship("Lote", back_populates="local")
