from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.eventos import (
    EventoPrincipalCreate,
    SubeventoCreate,
    EventoUpdate,
    EventoRead,
    EventoDetalheRead,
)
from app.services.eventos_service import EventoService

router = APIRouter(prefix="/eventos", tags=["Eventos"])
service = EventoService()


@router.get("", response_model=list[EventoRead])
def listar(
    cliente_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    q: str | None = Query(default=None),
    tipo_evento: str | None = Query(default=None, description="principal|subevento"),
    evento_pai_id: int | None = Query(default=None),
    somente_principais: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    try:
        return service.list(
            db,
            cliente_id=cliente_id,
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
            q=q,
            tipo_evento=tipo_evento,
            evento_pai_id=evento_pai_id,
            somente_principais=somente_principais,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{evento_id}", response_model=EventoDetalheRead)
def obter(evento_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, evento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=EventoDetalheRead, status_code=status.HTTP_201_CREATED)
def criar_evento_principal(payload: EventoPrincipalCreate, db: Session = Depends(get_db)):
    try:
        return service.create_principal(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "cliente" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/{evento_id}/subeventos", response_model=EventoDetalheRead, status_code=status.HTTP_201_CREATED)
def criar_subevento(
    evento_id: int,
    payload: SubeventoCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_subevento(db, evento_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.get("/{evento_id}/subeventos", response_model=list[EventoRead])
def listar_subeventos(evento_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_subeventos(db, evento_id)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.put("/{evento_id}", response_model=EventoDetalheRead)
def atualizar(evento_id: int, payload: EventoUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, evento_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(evento_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, evento_id)
        return None
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )