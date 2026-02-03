from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.compras import (
    CompraCreate, CompraUpdate, CompraRead,
    CompraConfirmarRequest, CompraConfirmarResponse
)
from app.schemas.compras_itens import CompraItemCreate, CompraItemUpdate, CompraItemRead
from app.services.compras_service import ComprasService
from app.services.compras_itens_service import ComprasItensService

router = APIRouter(prefix="/compras", tags=["Compras"])
service = ComprasService()
itens_service = ComprasItensService()


@router.get("", response_model=list[CompraRead])
def listar(
    fornecedor_id: int | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    return service.list(db, fornecedor_id=fornecedor_id, status=status_)


@router.get("/{compra_id}", response_model=CompraRead)
def obter(compra_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, compra_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CompraRead, status_code=status.HTTP_201_CREATED)
def criar(payload: CompraCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "inválido" in msg.lower() else 400, detail=msg)


@router.put("/{compra_id}", response_model=CompraRead)
def atualizar(compra_id: int, payload: CompraUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, compra_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)


@router.delete("/{compra_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(compra_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, compra_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------- Itens da compra --------
@router.get("/{compra_id}/itens", response_model=list[CompraItemRead])
def listar_itens(compra_id: int, db: Session = Depends(get_db)):
    try:
        return itens_service.list_by_compra(db, compra_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{compra_id}/itens", response_model=CompraItemRead, status_code=status.HTTP_201_CREATED)
def criar_item(compra_id: int, payload: CompraItemCreate, db: Session = Depends(get_db)):
    try:
        return itens_service.create(db, compra_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)


@router.put("/itens/{item_id}", response_model=CompraItemRead)
def atualizar_item(item_id: int, payload: CompraItemUpdate, db: Session = Depends(get_db)):
    try:
        return itens_service.update(db, item_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_item(item_id: int, db: Session = Depends(get_db)):
    try:
        itens_service.delete(db, item_id)
        return None
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


# -------- Confirmar (gera estoque) --------
@router.post("/{compra_id}/confirmar", response_model=CompraConfirmarResponse)
def confirmar(compra_id: int, payload: CompraConfirmarRequest, db: Session = Depends(get_db)):
    try:
        return service.confirmar(db, compra_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)
