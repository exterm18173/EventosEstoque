from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class ProdutoCategoria(Base):
    __tablename__ = "produtos_categorias"
    __table_args__ = (UniqueConstraint("produto_id", "categoria_id", name="uq_produto_categoria"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias_produto.id"), nullable=False, index=True)

    produto = relationship("Produto", back_populates="tags")
    categoria = relationship("CategoriaProduto", back_populates="produto_tags")
