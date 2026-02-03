from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.lotes import Lote
from app.models.produtos import Produto
from app.models.locais import Local
from app.schemas.lotes import LoteCreate, LoteUpdate


class LoteService:
    def list(
        self,
        db: Session,
        *,
        produto_id: int | None = None,
        local_id: int | None = None,
        validade_ate: str | None = None,  # YYYY-MM-DD (MVP)
        q: str | None = None,
    ) -> list[Lote]:
        stmt = select(Lote)

        if produto_id is not None:
            stmt = stmt.where(Lote.produto_id == produto_id)

        if local_id is not None:
            stmt = stmt.where(Lote.local_id == local_id)

        if validade_ate:
            # filtro simples; depois a gente melhora p/ date de verdade
            stmt = stmt.where(Lote.validade <= validade_ate)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Lote.codigo_lote.ilike(like))

        stmt = stmt.order_by(Lote.validade.asc().nulls_last(), Lote.codigo_lote.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, lote_id: int) -> Lote:
        obj = db.get(Lote, lote_id)
        if not obj:
            raise ValueError("Lote não encontrado.")
        return obj

    def create(self, db: Session, data: LoteCreate) -> Lote:
        produto = db.get(Produto, data.produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")

        if not produto.controla_lote:
            raise ValueError("Este produto não controla lote. Ative 'controla_lote' para usar lotes.")

        if not db.get(Local, data.local_id):
            raise ValueError("Local inválido.")

        # evitar duplicar mesmo lote no mesmo local para o mesmo produto (bom pro MVP)
        exists = db.execute(
            select(Lote).where(
                Lote.produto_id == data.produto_id,
                Lote.local_id == data.local_id,
                Lote.codigo_lote == data.codigo_lote.strip(),
            )
        ).scalar_one_or_none()
        if exists:
            raise ValueError("Já existe um lote com esse código para este produto neste local.")

        obj = Lote(
            produto_id=data.produto_id,
            local_id=data.local_id,
            codigo_lote=data.codigo_lote.strip(),
            validade=data.validade,
            quantidade_base_atual=float(data.quantidade_base_atual or 0),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, lote_id: int, data: LoteUpdate) -> Lote:
        obj = self.get(db, lote_id)

        if data.produto_id is not None:
            produto = db.get(Produto, data.produto_id)
            if not produto:
                raise ValueError("Produto não encontrado.")
            if not produto.controla_lote:
                raise ValueError("Este produto não controla lote. Ative 'controla_lote' para usar lotes.")
            obj.produto_id = data.produto_id

        if data.local_id is not None:
            if not db.get(Local, data.local_id):
                raise ValueError("Local inválido.")
            obj.local_id = data.local_id

        if data.codigo_lote is not None:
            obj.codigo_lote = data.codigo_lote.strip()

        if data.validade is not None or "validade" in data.model_fields_set:
            obj.validade = data.validade

        if data.quantidade_base_atual is not None or "quantidade_base_atual" in data.model_fields_set:
            obj.quantidade_base_atual = float(data.quantidade_base_atual or 0)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, lote_id: int) -> None:
        obj = self.get(db, lote_id)
        db.delete(obj)
        db.commit()

    def list_by_produto(self, db: Session, produto_id: int) -> list[Lote]:
        produto = db.get(Produto, produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")
        stmt = select(Lote).where(Lote.produto_id == produto_id).order_by(Lote.validade.asc().nulls_last())
        return list(db.execute(stmt).scalars().all())
