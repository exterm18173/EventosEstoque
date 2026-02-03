from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.aluguel_itens import AluguelItem
from app.models.alugueis import Aluguel
from app.models.produtos import Produto

from app.schemas.aluguel_itens import AluguelItemCreate, AluguelItemUpdate


class AluguelItensService:
    def list_by_aluguel(self, db: Session, aluguel_id: int) -> list[AluguelItem]:
        if not db.get(Aluguel, aluguel_id):
            raise ValueError("Aluguel não encontrado.")
        stmt = select(AluguelItem).where(AluguelItem.aluguel_id == aluguel_id).order_by(AluguelItem.id.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, item_id: int) -> AluguelItem:
        obj = db.get(AluguelItem, item_id)
        if not obj:
            raise ValueError("Item do aluguel não encontrado.")
        return obj

    def create(self, db: Session, aluguel_id: int, data: AluguelItemCreate) -> AluguelItem:
        aluguel = db.get(Aluguel, aluguel_id)
        if not aluguel:
            raise ValueError("Aluguel não encontrado.")
        if aluguel.status in {"cancelado", "devolvido"}:
            raise ValueError("Não é possível adicionar itens neste status.")

        produto = db.get(Produto, data.produto_id)
        if not produto:
            raise ValueError("Produto inválido.")
        if not produto.eh_alugavel:
            raise ValueError("Produto não está marcado como alugável (eh_alugavel=false).")

        obj = AluguelItem(
            aluguel_id=aluguel_id,
            produto_id=data.produto_id,
            quantidade_base=float(data.quantidade_base),
            quantidade_devolvida_base=0.0,
            valor_unitario=data.valor_unitario,
            status_item=data.status_item.strip() if data.status_item else "pendente",
            observacao=data.observacao,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, item_id: int, data: AluguelItemUpdate) -> AluguelItem:
        obj = self.get(db, item_id)

        if data.produto_id is not None:
            produto = db.get(Produto, data.produto_id)
            if not produto:
                raise ValueError("Produto inválido.")
            if not produto.eh_alugavel:
                raise ValueError("Produto não está marcado como alugável.")
            obj.produto_id = data.produto_id

        if data.quantidade_base is not None:
            obj.quantidade_base = float(data.quantidade_base)

        if data.quantidade_devolvida_base is not None or "quantidade_devolvida_base" in data.model_fields_set:
            obj.quantidade_devolvida_base = float(data.quantidade_devolvida_base or 0)

        if data.valor_unitario is not None or "valor_unitario" in data.model_fields_set:
            obj.valor_unitario = data.valor_unitario

        if data.status_item is not None:
            obj.status_item = data.status_item.strip()

        if data.observacao is not None or "observacao" in data.model_fields_set:
            obj.observacao = data.observacao

        # regra simples: devolvida não pode passar do total
        if obj.quantidade_devolvida_base > obj.quantidade_base + 1e-9:
            raise ValueError("quantidade_devolvida_base não pode ser maior que quantidade_base.")

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, item_id: int) -> None:
        obj = self.get(db, item_id)
        db.delete(obj)
        db.commit()
