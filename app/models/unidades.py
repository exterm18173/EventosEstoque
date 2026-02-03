from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Unidade(Base, TimestampMixin):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sigla: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(120), nullable=False)

    produtos_base = relationship("Produto", back_populates="unidade_base")
    embalagens = relationship("ProdutoEmbalagem", back_populates="unidade")
