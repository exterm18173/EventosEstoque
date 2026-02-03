from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.clientes import ClienteCreate, ClienteUpdate, ClienteRead
from app.services.clientes_service import ClienteService

router = APIRouter(prefix="/clientes", tags=["Clientes"])
service = ClienteService()


@router.get("", response_model=list[ClienteRead])
def listar(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.list(db, q=q)


@router.get("/{cliente_id}", response_model=ClienteRead)
def obter(cliente_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, cliente_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def criar(payload: ClienteCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.put("/{cliente_id}", response_model=ClienteRead)
def atualizar(cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, cliente_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(cliente_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, cliente_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
