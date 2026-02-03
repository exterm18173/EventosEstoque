from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.marcas import MarcaCreate, MarcaUpdate, MarcaRead
from app.services.marcas_service import MarcaService

router = APIRouter(prefix="/marcas", tags=["Marcas"])
service = MarcaService()


@router.get("", response_model=list[MarcaRead])
def listar(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.list(db, q=q)


@router.get("/{marca_id}", response_model=MarcaRead)
def obter(marca_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, marca_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=MarcaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: MarcaCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{marca_id}", response_model=MarcaRead)
def atualizar(marca_id: int, payload: MarcaUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, marca_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)


@router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(marca_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, marca_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
