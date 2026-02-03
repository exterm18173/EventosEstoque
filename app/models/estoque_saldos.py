from sqlalchemy import Integer, Float, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .base import Base

class EstoqueSaldo(Base):
    __tablename__ = "estoque_saldos"
    __table_args__ = (UniqueConstraint("produto_id", "local_id", name="uq_saldo_produto_local"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("locais.id"), nullable=False, index=True)
    quantidade_base: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    produto = relationship("Produto", back_populates="saldos")
    local = relationship("Local", back_populates="saldos")
