from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.unidades import UnidadeCreate, UnidadeUpdate, UnidadeRead
from app.services.unidades_service import UnidadeService

router = APIRouter(prefix="/unidades", tags=["Unidades"])
service = UnidadeService()


@router.get("", response_model=list[UnidadeRead])
def listar_unidades(db: Session = Depends(get_db)):
    return service.list(db)


@router.get("/{unidade_id}", response_model=UnidadeRead)
def obter_unidade(unidade_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, unidade_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=UnidadeRead, status_code=status.HTTP_201_CREATED)
def criar_unidade(payload: UnidadeCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{unidade_id}", response_model=UnidadeRead)
def atualizar_unidade(unidade_id: int, payload: UnidadeUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, unidade_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)


@router.delete("/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_unidade(unidade_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, unidade_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
