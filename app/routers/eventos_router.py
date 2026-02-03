from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.eventos import EventoCreate, EventoUpdate, EventoRead
from app.services.eventos_service import EventoService

router = APIRouter(prefix="/eventos", tags=["Eventos"])
service = EventoService()


@router.get("", response_model=list[EventoRead])
def listar(
    cliente_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    data_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(default=None, description="YYYY-MM-DD"),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        cliente_id=cliente_id,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim,
        q=q,
    )


@router.get("/{evento_id}", response_model=EventoRead)
def obter(evento_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, evento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=EventoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: EventoCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "cliente" in msg.lower() else 400, detail=msg)


@router.put("/{evento_id}", response_model=EventoRead)
def atualizar(evento_id: int, payload: EventoUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, evento_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(evento_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, evento_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
