from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    perfil: Mapped[str] = mapped_column(String(40), default="admin", nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    movimentacoes = relationship("Movimentacao", back_populates="usuario")
    compras = relationship("Compra", back_populates="usuario")
    nfe_documentos = relationship("NfeDocumento", back_populates="usuario")
