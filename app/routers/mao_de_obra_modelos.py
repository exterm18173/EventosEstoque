from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.mao_de_obra_modelos_service import MaoDeObraModelosService
from app.services.mao_de_obra_service import MaoDeObraService

from app.schemas.mao_de_obra import MaoDeObraResponse
from app.schemas.mao_de_obra_modelos import (
    MaoDeObraModeloCreate,
    MaoDeObraModeloReplace,
    MaoDeObraModeloRead,
    MaoDeObraModeloListItem,
    MaoDeObraModeloFromEventoInput,
    AplicarModeloPayload,
)

service = MaoDeObraModelosService()
evento_service = MaoDeObraService()

router = APIRouter(prefix="/mao-de-obra/modelos", tags=["Mão de Obra - Modelos"])


@router.get("", response_model=list[MaoDeObraModeloListItem])
def listar_modelos(
    tipo_evento: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list_modelos(db, tipo_evento=tipo_evento)


@router.post("", response_model=MaoDeObraModeloRead)
def criar_modelo(
    payload: MaoDeObraModeloCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_modelo(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{modelo_id}", response_model=MaoDeObraModeloRead)
def obter_modelo(
    modelo_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.get_modelo(db, modelo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{modelo_id}", response_model=MaoDeObraModeloRead)
def substituir_modelo(
    modelo_id: int,
    payload: MaoDeObraModeloReplace,
    db: Session = Depends(get_db),
):
    try:
        return service.replace_modelo(db, modelo_id, payload)
    except ValueError as e:
        msg = str(e)
        if "não encontrado" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)


@router.delete("/{modelo_id}")
def deletar_modelo(
    modelo_id: int,
    db: Session = Depends(get_db),
):
    try:
        service.delete_modelo(db, modelo_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/from-evento/{evento_id}", response_model=MaoDeObraModeloRead)
def salvar_modelo_a_partir_do_evento(
    evento_id: int,
    payload: MaoDeObraModeloFromEventoInput,
    db: Session = Depends(get_db),
):
    try:
        return service.create_from_evento(db, evento_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/apply/{modelo_id}/evento/{evento_id}", response_model=MaoDeObraResponse)
def aplicar_modelo_no_evento(
    modelo_id: int,
    evento_id: int,
    payload: AplicarModeloPayload,
    db: Session = Depends(get_db),
):
    try:
        grupos = service.apply_modelo(db, evento_id, modelo_id, payload)
        total = evento_service.total_evento(db, evento_id)
        return MaoDeObraResponse(evento_id=evento_id, grupos=grupos, total=total)
    except ValueError as e:
        msg = str(e)
        if "não encontrado" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
