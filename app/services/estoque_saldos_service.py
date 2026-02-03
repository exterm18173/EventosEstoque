from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.estoque_saldos import EstoqueSaldo
from app.models.produtos import Produto
from app.models.produtos_base import ProdutoBase


class EstoqueSaldosService:
    def list(
        self,
        db: Session,
        *,
        local_id: int | None = None,
        produto_id: int | None = None,
        produto_base_id: int | None = None,
        q: str | None = None,
    ) -> list[EstoqueSaldo]:
        stmt = select(EstoqueSaldo).join(Produto, Produto.id == EstoqueSaldo.produto_id)

        if local_id is not None:
            stmt = stmt.where(EstoqueSaldo.local_id == local_id)

        if produto_id is not None:
            stmt = stmt.where(EstoqueSaldo.produto_id == produto_id)

        if produto_base_id is not None:
            stmt = stmt.where(Produto.produto_base_id == produto_base_id)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Produto.nome_comercial.ilike(like))

        stmt = stmt.order_by(Produto.nome_comercial.asc(), EstoqueSaldo.local_id.asc())
        return list(db.execute(stmt).scalars().all())

    def by_produto(self, db: Session, produto_id: int) -> list[EstoqueSaldo]:
        # valida produto
        if not db.get(Produto, produto_id):
            raise ValueError("Produto não encontrado.")

        stmt = (
            select(EstoqueSaldo)
            .where(EstoqueSaldo.produto_id == produto_id)
            .order_by(EstoqueSaldo.local_id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def consolidado_produto_base(self, db: Session, *, local_id: int | None = None) -> list[dict]:
        # agrupa por produto_base_id somando os saldos
        stmt = (
            select(
                Produto.produto_base_id.label("produto_base_id"),
                func.coalesce(func.sum(EstoqueSaldo.quantidade_base), 0.0).label("total"),
            )
            .select_from(EstoqueSaldo)
            .join(Produto, Produto.id == EstoqueSaldo.produto_id)
            .group_by(Produto.produto_base_id)
            .order_by(Produto.produto_base_id.asc())
        )

        if local_id is not None:
            stmt = stmt.where(EstoqueSaldo.local_id == local_id)

        rows = list(db.execute(stmt).all())

        # valida que o produto_base existe (opcional, mas útil)
        ids = [r.produto_base_id for r in rows if r.produto_base_id is not None]
        if ids:
            existentes = set(db.execute(select(ProdutoBase.id).where(ProdutoBase.id.in_(ids))).scalars().all())
        else:
            existentes = set()

        out: list[dict] = []
        for r in rows:
            pb_id = int(r.produto_base_id) if r.produto_base_id is not None else None
            if pb_id is None:
                continue
            if pb_id not in existentes:
                continue
            out.append(
                {
                    "produto_base_id": pb_id,
                    "total_quantidade_base": float(r.total or 0.0),
                    "local_id": local_id,
                }
            )
        return out
