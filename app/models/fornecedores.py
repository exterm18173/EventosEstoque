from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

class Fornecedor(Base, TimestampMixin):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    documento: Mapped[str] = mapped_column(String(40), nullable=True, index=True)
    telefone: Mapped[str] = mapped_column(String(40), nullable=True)
    email: Mapped[str] = mapped_column(String(160), nullable=True)

    compras = relationship("Compra", back_populates="fornecedor")
    nfe_documentos = relationship("NfeDocumento", back_populates="fornecedor")
