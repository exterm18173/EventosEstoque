from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.locais import LocalCreate, LocalUpdate, LocalRead
from app.services.locais_service import LocalService

router = APIRouter(prefix="/locais", tags=["Locais"])
service = LocalService()


@router.get("", response_model=list[LocalRead])
def listar(
    q: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(db, q=q, tipo=tipo)


@router.get("/{local_id}", response_model=LocalRead)
def obter(local_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, local_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=LocalRead, status_code=status.HTTP_201_CREATED)
def criar(payload: LocalCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.put("/{local_id}", response_model=LocalRead)
def atualizar(local_id: int, payload: LocalUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, local_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{local_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(local_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, local_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
