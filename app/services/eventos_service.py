from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.clientes import Cliente
from app.models.eventos import Evento
from app.schemas.eventos import (
    EventoPrincipalCreate,
    SubeventoCreate,
    EventoUpdate,
)


class EventoService:
    TIPOS_VALIDOS = {"principal", "subevento"}

    def list(
        self,
        db: Session,
        *,
        cliente_id: int | None = None,
        status: str | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        q: str | None = None,
        tipo_evento: str | None = None,
        evento_pai_id: int | None = None,
        somente_principais: bool = False,
    ) -> list[Evento]:
        stmt = (
            select(Evento)
            .options(
                selectinload(Evento.evento_pai),
                selectinload(Evento.subeventos),
            )
        )

        if cliente_id is not None:
            stmt = stmt.where(Evento.cliente_id == cliente_id)

        if status:
            stmt = stmt.where(Evento.status == status.strip())

        if tipo_evento:
            tipo_limpo = tipo_evento.strip()
            if tipo_limpo not in self.TIPOS_VALIDOS:
                raise ValueError("tipo_evento inválido. Use 'principal' ou 'subevento'.")
            stmt = stmt.where(Evento.tipo_evento == tipo_limpo)

        if somente_principais:
            stmt = stmt.where(Evento.tipo_evento == "principal")

        if evento_pai_id is not None:
            stmt = stmt.where(Evento.evento_pai_id == evento_pai_id)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Evento.nome.ilike(like))

        if data_inicio:
            stmt = stmt.where(Evento.data_inicio >= data_inicio)

        if data_fim:
            stmt = stmt.where(Evento.data_inicio <= data_fim)

        stmt = stmt.order_by(Evento.data_inicio.desc(), Evento.id.desc())
        return list(db.execute(stmt).scalars().unique().all())

    def get(self, db: Session, evento_id: int) -> Evento:
        stmt = (
            select(Evento)
            .options(
                selectinload(Evento.evento_pai),
                selectinload(Evento.subeventos),
            )
            .where(Evento.id == evento_id)
        )
        obj = db.execute(stmt).scalar_one_or_none()

        if not obj:
            raise ValueError("Evento não encontrado.")

        return obj

    def create_principal(self, db: Session, data: EventoPrincipalCreate) -> Evento:
        cliente = db.get(Cliente, data.cliente_id)
        if not cliente:
            raise ValueError("Cliente inválido.")

        if data.data_fim and data.data_fim < data.data_inicio:
            raise ValueError("data_fim não pode ser menor que data_inicio.")

        obj = Evento(
            cliente_id=data.cliente_id,
            nome=data.nome.strip(),
            data_inicio=data.data_inicio,
            data_fim=data.data_fim or data.data_inicio,
            status=data.status.strip() if data.status else "planejado",
            local_evento=data.local_evento.strip() if data.local_evento else None,
            observacao=data.observacao,
            receita=data.receita,
            receita_convite_extra=data.receita_convite_extra,
            tipo_evento="principal",
            evento_pai_id=None,
        )

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return self.get(db, obj.id)

    def create_subevento(
        self,
        db: Session,
        evento_pai_id: int,
        data: SubeventoCreate,
    ) -> Evento:
        evento_pai = self.get(db, evento_pai_id)

        if evento_pai.tipo_evento != "principal":
            raise ValueError("Só é permitido criar subevento dentro de um evento principal.")

        if data.data_fim and data.data_fim < data.data_inicio:
            raise ValueError("data_fim não pode ser menor que data_inicio.")

        obj = Evento(
            cliente_id=evento_pai.cliente_id,
            nome=data.nome.strip(),
            data_inicio=data.data_inicio,
            data_fim=data.data_fim or data.data_inicio,
            status=data.status.strip() if data.status else "planejado",
            local_evento=data.local_evento.strip() if data.local_evento else None,
            observacao=data.observacao,
            receita=data.receita,
            receita_convite_extra=data.receita_convite_extra,
            tipo_evento="subevento",
            evento_pai_id=evento_pai.id,
        )

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return self.get(db, obj.id)

    def update(self, db: Session, evento_id: int, data: EventoUpdate) -> Evento:
        obj = self.get(db, evento_id)

        if data.nome is not None:
            obj.nome = data.nome.strip()

        if data.data_inicio is not None:
            obj.data_inicio = data.data_inicio

        if data.data_fim is not None or "data_fim" in data.model_fields_set:
            obj.data_fim = data.data_fim or obj.data_inicio

        if obj.data_fim and obj.data_fim < obj.data_inicio:
            raise ValueError("data_fim não pode ser menor que data_inicio.")

        if data.status is not None:
            obj.status = data.status.strip()

        if data.local_evento is not None:
            obj.local_evento = data.local_evento.strip() if data.local_evento else None

        if data.observacao is not None or "observacao" in data.model_fields_set:
            obj.observacao = data.observacao

        if data.receita is not None or "receita" in data.model_fields_set:
            obj.receita = data.receita

        if data.receita_convite_extra is not None or "receita_convite_extra" in data.model_fields_set:
            obj.receita_convite_extra = data.receita_convite_extra

        db.commit()
        db.refresh(obj)
        return self.get(db, obj.id)

    def delete(self, db: Session, evento_id: int) -> None:
        obj = self.get(db, evento_id)

        if obj.tipo_evento == "principal" and obj.total_subeventos > 0:
            raise ValueError(
                "Este evento principal possui subeventos vinculados. Exclua os subeventos primeiro."
            )

        db.delete(obj)
        db.commit()

    def list_subeventos(self, db: Session, evento_pai_id: int) -> list[Evento]:
        evento_pai = self.get(db, evento_pai_id)

        if evento_pai.tipo_evento != "principal":
            raise ValueError("O evento informado não é um evento principal.")

        stmt = (
            select(Evento)
            .options(
                selectinload(Evento.evento_pai),
                selectinload(Evento.subeventos),
            )
            .where(Evento.evento_pai_id == evento_pai_id)
            .order_by(Evento.data_inicio.asc(), Evento.id.asc())
        )
        return list(db.execute(stmt).scalars().unique().all())