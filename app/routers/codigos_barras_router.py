from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.codigos_barras import (
    CodigoBarrasCreate,
    CodigoBarrasUpdate,
    CodigoBarrasRead,
    BarcodeLookupResponse,
)
from app.services.codigos_barras_service import CodigoBarrasService

router = APIRouter(tags=["Códigos de Barras"])
service = CodigoBarrasService()


@router.get("/produtos/{produto_id}/codigos-barras", response_model=list[CodigoBarrasRead])
def listar_por_produto(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_by_produto(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/produtos/{produto_id}/codigos-barras",
    response_model=CodigoBarrasRead,
    status_code=status.HTTP_201_CREATED,
)
def criar(produto_id: int, payload: CodigoBarrasCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, produto_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "produto não encontrado" in msg.lower() else 400, detail=msg)


@router.put("/codigos-barras/{barcode_id}", response_model=CodigoBarrasRead)
def atualizar(barcode_id: int, payload: CodigoBarrasUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, barcode_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/codigos-barras/{barcode_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(barcode_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, barcode_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/codigos-barras/{barcode_id}/definir-principal", response_model=CodigoBarrasRead)
def definir_principal(barcode_id: int, db: Session = Depends(get_db)):
    try:
        return service.definir_principal(db, barcode_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/codigos-barras/lookup/{codigo}", response_model=BarcodeLookupResponse)
def lookup(codigo: str, db: Session = Depends(get_db)):
    try:
        return service.lookup(db, codigo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
