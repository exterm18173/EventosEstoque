from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.setores_consumo import SetorConsumoCreate, SetorConsumoRead
from app.services.setores_consumo_service import SetoresConsumoService

router = APIRouter(prefix="/setores-consumo", tags=["Setores de Consumo"])
service = SetoresConsumoService()


@router.get("", response_model=list[SetorConsumoRead])
def listar(db: Session = Depends(get_db)):
    return service.list(db)


@router.get("/{setor_id}", response_model=SetorConsumoRead)
def obter(setor_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, setor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=SetorConsumoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: SetorConsumoCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))