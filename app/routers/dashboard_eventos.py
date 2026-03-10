from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_eventos_service import DashboardEventosService
from app.schemas.dashboard_eventos import (
    DashboardEventosResumoResponse,
    DashboardKpis,
    DashboardEventoResumo,
    DashboardEventoDetail,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
service = DashboardEventosService()


@router.get("/eventos", response_model=DashboardEventosResumoResponse)
def eventos_resumo(
    from_: Optional[date] = Query(default=None, alias="from"),
    to: Optional[date] = Query(default=None, alias="to"),
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total_items, kpis, eventos = service.resumo(
        db,
        from_=from_,
        to=to,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )

    return DashboardEventosResumoResponse(
        total_items=total_items,
        kpis=DashboardKpis(**kpis),
        eventos=[DashboardEventoResumo(**e) for e in eventos],
    )


@router.get("/eventos/{evento_id}", response_model=DashboardEventoDetail)
def evento_detalhe(evento_id: int, db: Session = Depends(get_db)):
    data = service.detalhe(db, evento_id)
    if not data:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return DashboardEventoDetail(**data)