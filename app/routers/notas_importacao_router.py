from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.nota_importacao import (
    NotaImportacaoConfirmarCompraRequest,
    NotaImportacaoConfirmarCompraResponse,
    NotaImportacaoGerarCompraRequest,
    NotaImportacaoGerarCompraResponse,
    NotaImportacaoPreviewResponse,
)
from app.services.nota_importacao_service import NotaImportacaoService

router = APIRouter(prefix="/notas-importacao", tags=["Fiscal - Importação"])

service = NotaImportacaoService()


@router.get("/{nota_id}/preview", response_model=NotaImportacaoPreviewResponse)
def preview(
    nota_id: int,
    db: Session = Depends(get_db),
):
    try:
        data = service.preview(db, nota_id=nota_id)
        return NotaImportacaoPreviewResponse(**data)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/{nota_id}/gerar-compra", response_model=NotaImportacaoGerarCompraResponse)
def gerar_compra(
    nota_id: int,
    payload: NotaImportacaoGerarCompraRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.gerar_compra(
            db,
            nota_id=nota_id,
            usuario_id=payload.usuario_id,
            fornecedor_id=payload.fornecedor_id,
            observacao=payload.observacao,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/{nota_id}/confirmar-compra", response_model=NotaImportacaoConfirmarCompraResponse)
def confirmar_compra(
    nota_id: int,
    payload: NotaImportacaoConfirmarCompraRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.confirmar_compra(
            db,
            nota_id=nota_id,
            usuario_id=payload.usuario_id,
            local_destino_id=payload.local_destino_id,
            origem=payload.origem,
            observacao=payload.observacao,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )