from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.produtos_base import ProdutoBase
from app.models.categorias_produto import CategoriaProduto
from app.models.produtos import Produto
from app.models.estoque_saldos import EstoqueSaldo
from app.schemas.produtos_base import ProdutoBaseCreate, ProdutoBaseUpdate


class ProdutoBaseService:
    def list(
        self,
        db: Session,
        *,
        categoria_id: int | None = None,
        ativo: bool | None = None,
        q: str | None = None,
    ) -> list[ProdutoBase]:
        stmt = select(ProdutoBase)

        if categoria_id is not None:
            stmt = stmt.where(ProdutoBase.categoria_principal_id == categoria_id)

        if ativo is not None:
            stmt = stmt.where(ProdutoBase.ativo == ativo)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(ProdutoBase.nome_base.ilike(like))

        stmt = stmt.order_by(ProdutoBase.nome_base.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, produto_base_id: int) -> ProdutoBase:
        obj = db.get(ProdutoBase, produto_base_id)
        if not obj:
            raise ValueError("Produto base não encontrado.")
        return obj

    def create(self, db: Session, data: ProdutoBaseCreate) -> ProdutoBase:
        # valida categoria principal se vier
        if data.categoria_principal_id is not None:
            cat = db.get(CategoriaProduto, data.categoria_principal_id)
            if not cat:
                raise ValueError("Categoria principal inválida.")

        obj = ProdutoBase(
            nome_base=data.nome_base.strip(),
            categoria_principal_id=data.categoria_principal_id,
            descricao=(data.descricao.strip() if data.descricao else None),
            ativo=data.ativo,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, produto_base_id: int, data: ProdutoBaseUpdate) -> ProdutoBase:
        obj = self.get(db, produto_base_id)

        if data.nome_base is not None:
            obj.nome_base = data.nome_base.strip()

        if data.categoria_principal_id is not None:
            if data.categoria_principal_id is not None:
                cat = db.get(CategoriaProduto, data.categoria_principal_id)
                if not cat:
                    raise ValueError("Categoria principal inválida.")
            obj.categoria_principal_id = data.categoria_principal_id

        if data.descricao is not None:
            obj.descricao = data.descricao.strip() if data.descricao else None

        if data.ativo is not None:
            obj.ativo = data.ativo

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, produto_base_id: int) -> None:
        obj = self.get(db, produto_base_id)

        # segurança: se tiver variações, impedir delete (pode trocar por soft delete)
        has_variacoes = db.execute(
            select(Produto.id).where(Produto.produto_base_id == produto_base_id).limit(1)
        ).first()
        if has_variacoes:
            raise ValueError("Não é possível excluir: existem variações vinculadas a este produto base.")

        db.delete(obj)
        db.commit()

    def variacoes(self, db: Session, produto_base_id: int) -> list[Produto]:
        self.get(db, produto_base_id)  # valida
        stmt = select(Produto).where(Produto.produto_base_id == produto_base_id).order_by(Produto.nome_comercial.asc())
        return list(db.execute(stmt).scalars().all())

    def estoque_consolidado(self, db: Session, produto_base_id: int, local_id: int | None = None) -> float:
        self.get(db, produto_base_id)  # valida

        stmt = (
            select(func.coalesce(func.sum(EstoqueSaldo.quantidade_base), 0.0))
            .select_from(EstoqueSaldo)
            .join(Produto, Produto.id == EstoqueSaldo.produto_id)
            .where(Produto.produto_base_id == produto_base_id)
        )
        if local_id is not None:
            stmt = stmt.where(EstoqueSaldo.local_id == local_id)

        total = db.execute(stmt).scalar_one()
        return float(total or 0.0)
