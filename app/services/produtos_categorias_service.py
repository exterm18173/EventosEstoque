from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.produtos import Produto
from app.models.categorias_produto import CategoriaProduto
from app.models.produtos_categorias import ProdutoCategoria


class ProdutoCategoriaService:
    def list(self, db: Session, produto_id: int) -> list[ProdutoCategoria]:
        if not db.get(Produto, produto_id):
            raise ValueError("Produto não encontrado.")

        stmt = (
            select(ProdutoCategoria)
            .where(ProdutoCategoria.produto_id == produto_id)
            .order_by(ProdutoCategoria.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def add(self, db: Session, produto_id: int, categoria_id: int) -> ProdutoCategoria:
        if not db.get(Produto, produto_id):
            raise ValueError("Produto não encontrado.")
        if not db.get(CategoriaProduto, categoria_id):
            raise ValueError("Categoria não encontrada.")

        exists = db.execute(
            select(ProdutoCategoria).where(
                ProdutoCategoria.produto_id == produto_id,
                ProdutoCategoria.categoria_id == categoria_id,
            )
        ).scalar_one_or_none()
        if exists:
            return exists  # idempotente

        link = ProdutoCategoria(produto_id=produto_id, categoria_id=categoria_id)
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    def remove(self, db: Session, produto_id: int, categoria_id: int) -> None:
        if not db.get(Produto, produto_id):
            raise ValueError("Produto não encontrado.")
        if not db.get(CategoriaProduto, categoria_id):
            raise ValueError("Categoria não encontrada.")

        link = db.execute(
            select(ProdutoCategoria).where(
                ProdutoCategoria.produto_id == produto_id,
                ProdutoCategoria.categoria_id == categoria_id,
            )
        ).scalar_one_or_none()
        if not link:
            raise ValueError("Vínculo não encontrado.")

        db.delete(link)
        db.commit()
