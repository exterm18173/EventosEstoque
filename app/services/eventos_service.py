from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.eventos import Evento
from app.models.clientes import Cliente
from app.schemas.eventos import EventoCreate, EventoUpdate


class EventoService:
    def list(
        self,
        db: Session,
        *,
        cliente_id: int | None = None,
        status: str | None = None,
        data_inicio: str | None = None,  # YYYY-MM-DD (MVP)
        data_fim: str | None = None,     # YYYY-MM-DD (MVP)
        q: str | None = None,
    ) -> list[Evento]:
        stmt = select(Evento)

        if cliente_id is not None:
            stmt = stmt.where(Evento.cliente_id == cliente_id)

        if status is not None:
            stmt = stmt.where(Evento.status == status)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Evento.nome.ilike(like))

        # filtro por período (MVP)
        if data_inicio:
            stmt = stmt.where(Evento.data_inicio >= data_inicio)
        if data_fim:
            stmt = stmt.where(Evento.data_inicio <= data_fim)

        stmt = stmt.order_by(Evento.data_inicio.desc(), Evento.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, evento_id: int) -> Evento:
        obj = db.get(Evento, evento_id)
        if not obj:
            raise ValueError("Evento não encontrado.")
        return obj

    def create(self, db: Session, data: EventoCreate) -> Evento:
        if not db.get(Cliente, data.cliente_id):
            raise ValueError("Cliente inválido.")

        if data.data_fim and data.data_fim < data.data_inicio:
            raise ValueError("data_fim não pode ser menor que data_inicio.")

        obj = Evento(
            cliente_id=data.cliente_id,
            nome=data.nome.strip(),
            data_inicio=data.data_inicio,
            data_fim=data.data_fim,
            status=data.status.strip() if data.status else "planejado",
            local_evento=(data.local_evento.strip() if data.local_evento else None),
            observacao=data.observacao,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, evento_id: int, data: EventoUpdate) -> Evento:
        obj = self.get(db, evento_id)

        if data.cliente_id is not None:
            if not db.get(Cliente, data.cliente_id):
                raise ValueError("Cliente inválido.")
            obj.cliente_id = data.cliente_id

        if data.nome is not None:
            obj.nome = data.nome.strip()

        if data.data_inicio is not None:
            obj.data_inicio = data.data_inicio

        if data.data_fim is not None or "data_fim" in data.model_fields_set:
            obj.data_fim = data.data_fim

        # valida datas após updates
        if obj.data_fim and obj.data_fim < obj.data_inicio:
            raise ValueError("data_fim não pode ser menor que data_inicio.")

        if data.status is not None:
            obj.status = data.status.strip()

        if data.local_evento is not None:
            obj.local_evento = data.local_evento.strip() if data.local_evento else None

        if data.observacao is not None or "observacao" in data.model_fields_set:
            obj.observacao = data.observacao

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, evento_id: int) -> None:
        obj = self.get(db, evento_id)
        db.delete(obj)
        db.commit()
