from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Marca(Base, TimestampMixin):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)

    produtos = relationship("Produto", back_populates="marca")
