from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.mao_de_obra_service import MaoDeObraService
from app.schemas.mao_de_obra import (
    MaoDeObraInput,
    MaoDeObraAppendInput,
    MaoDeObraResponse,
    MaoDeObraItemRead,
    MaoDeObraItemUpdate,
    MaoDeObraResumoRead,
)

service = MaoDeObraService()
router = APIRouter(prefix="/mao-de-obra", tags=["Mão de Obra"])


# ============ REPLACE TOTAL (apaga e recria) ============
@router.put("/evento/{evento_id}", response_model=MaoDeObraResponse)
def salvar_evento(evento_id: int, payload: MaoDeObraInput, db: Session = Depends(get_db)):
    if payload.evento_id != evento_id:
        raise HTTPException(status_code=400, detail="evento_id do payload diferente da rota")

    try:
        grupos = service.upsert_evento(db, payload)
        total = service.total_evento(db, evento_id)
        return MaoDeObraResponse(evento_id=evento_id, grupos=grupos, total=total)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ APPEND EM LOTE (NOVO) ============
@router.post("/evento/{evento_id}/append", response_model=MaoDeObraResponse)
def append_evento(evento_id: int, payload: MaoDeObraAppendInput, db: Session = Depends(get_db)):
    """
    Lança em lote vários grupos e itens no evento, sem apagar os existentes.
    """
    try:
        grupos = service.append_evento(db, evento_id, payload)
        total = service.total_evento(db, evento_id)
        return MaoDeObraResponse(evento_id=evento_id, grupos=grupos, total=total)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ GETS ============
@router.get("/evento/{evento_id}", response_model=MaoDeObraResponse)
def obter_evento(evento_id: int, db: Session = Depends(get_db)):
    grupos = service.get_evento(db, evento_id)
    total = service.total_evento(db, evento_id)
    return MaoDeObraResponse(evento_id=evento_id, grupos=grupos, total=total)


@router.get("/evento/{evento_id}/resumo", response_model=MaoDeObraResumoRead)
def resumo_evento(evento_id: int, db: Session = Depends(get_db)):
    total = service.total_evento(db, evento_id)
    por_cat = service.por_categoria(db, evento_id)
    return MaoDeObraResumoRead(evento_id=evento_id, total=total, por_categoria=por_cat)


# ============ ITENS (update/delete) ============
@router.put("/itens/{item_id}", response_model=MaoDeObraItemRead)
def atualizar_item(item_id: int, payload: MaoDeObraItemUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_item(db, item_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/itens/{item_id}")
def deletar_item(item_id: int, db: Session = Depends(get_db)):
    service.delete_item(db, item_id)
    return {"ok": True}
