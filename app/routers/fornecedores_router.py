from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fornecedores import FornecedorCreate, FornecedorUpdate, FornecedorRead
from app.services.fornecedores_service import FornecedorService

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])
service = FornecedorService()


@router.get("", response_model=list[FornecedorRead])
def listar(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.list(db, q=q)


@router.get("/{fornecedor_id}", response_model=FornecedorRead)
def obter(fornecedor_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, fornecedor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=FornecedorRead, status_code=status.HTTP_201_CREATED)
def criar(payload: FornecedorCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.put("/{fornecedor_id}", response_model=FornecedorRead)
def atualizar(fornecedor_id: int, payload: FornecedorUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, fornecedor_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(fornecedor_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, fornecedor_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
