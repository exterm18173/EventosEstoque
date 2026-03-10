from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.nota_conciliacao import (
    NotaConciliacaoItemRead,
    NotaItemCriarProdutoRequest,
    NotaItemIgnorarRequest,
    NotaItemVincularProdutoRequest,
)
from app.services.nota_conciliacao_service import NotaConciliacaoService

router = APIRouter(prefix="/notas-conciliacao", tags=["Fiscal - Conciliação"])

service = NotaConciliacaoService()


@router.post("/itens/{item_id}/auto", response_model=NotaConciliacaoItemRead)
def auto_conciliar_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.auto_conciliar_item(db, item_id)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/itens/{item_id}/vincular-produto", response_model=NotaConciliacaoItemRead)
def vincular_produto(
    item_id: int,
    payload: NotaItemVincularProdutoRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.vincular_produto(db, item_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() or "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/itens/{item_id}/criar-produto", response_model=NotaConciliacaoItemRead)
def criar_produto(
    item_id: int,
    payload: NotaItemCriarProdutoRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.criar_produto_e_vincular(db, item_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() or "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/itens/{item_id}/ignorar", response_model=NotaConciliacaoItemRead)
def ignorar_item(
    item_id: int,
    payload: NotaItemIgnorarRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.ignorar_item(db, item_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )