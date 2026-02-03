from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.alugueis import Aluguel
from app.models.clientes import Cliente
from app.models.eventos import Evento
from app.schemas.alugueis import AluguelCreate, AluguelUpdate


class AlugueisService:
    def list(self, db: Session, *, cliente_id: int | None = None, status: str | None = None) -> list[Aluguel]:
        stmt = select(Aluguel)
        if cliente_id is not None:
            stmt = stmt.where(Aluguel.cliente_id == cliente_id)
        if status is not None:
            stmt = stmt.where(Aluguel.status == status)
        stmt = stmt.order_by(Aluguel.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, aluguel_id: int) -> Aluguel:
        obj = db.get(Aluguel, aluguel_id)
        if not obj:
            raise ValueError("Aluguel não encontrado.")
        return obj

    def create(self, db: Session, data: AluguelCreate) -> Aluguel:
        if not db.get(Cliente, data.cliente_id):
            raise ValueError("Cliente inválido.")
        if data.evento_id is not None and not db.get(Evento, data.evento_id):
            raise ValueError("Evento inválido.")
        if data.data_devolucao_prevista < data.data_saida_prevista:
            raise ValueError("data_devolucao_prevista não pode ser menor que data_saida_prevista.")

        obj = Aluguel(
            cliente_id=data.cliente_id,
            evento_id=data.evento_id,
            data_saida_prevista=data.data_saida_prevista,
            data_devolucao_prevista=data.data_devolucao_prevista,
            data_devolucao_real=data.data_devolucao_real,
            status=data.status.strip() if data.status else "aberto",
            valor_total=data.valor_total,
            observacao=data.observacao,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, aluguel_id: int, data: AluguelUpdate) -> Aluguel:
        obj = self.get(db, aluguel_id)

        if data.cliente_id is not None:
            if not db.get(Cliente, data.cliente_id):
                raise ValueError("Cliente inválido.")
            obj.cliente_id = data.cliente_id

        if data.evento_id is not None or "evento_id" in data.model_fields_set:
            if data.evento_id is not None and not db.get(Evento, data.evento_id):
                raise ValueError("Evento inválido.")
            obj.evento_id = data.evento_id

        if data.data_saida_prevista is not None:
            obj.data_saida_prevista = data.data_saida_prevista

        if data.data_devolucao_prevista is not None:
            obj.data_devolucao_prevista = data.data_devolucao_prevista

        if data.data_devolucao_real is not None or "data_devolucao_real" in data.model_fields_set:
            obj.data_devolucao_real = data.data_devolucao_real

        if obj.data_devolucao_prevista < obj.data_saida_prevista:
            raise ValueError("data_devolucao_prevista não pode ser menor que data_saida_prevista.")

        if data.status is not None:
            obj.status = data.status.strip()

        if data.valor_total is not None or "valor_total" in data.model_fields_set:
            obj.valor_total = data.valor_total

        if data.observacao is not None or "observacao" in data.model_fields_set:
            obj.observacao = data.observacao

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, aluguel_id: int) -> None:
        obj = self.get(db, aluguel_id)
        db.delete(obj)
        db.commit()
