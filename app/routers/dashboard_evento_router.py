from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_evento_service import DashboardEventoService
from app.schemas.dashboard_evento import DashboardEventoDashResponse 

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
service = DashboardEventoService()


@router.get("/eventos/{evento_id}/dash", response_model=DashboardEventoDashResponse)
def evento_dashboard(evento_id: int, db: Session = Depends(get_db)):
    data = service.get_dash(db, evento_id)
    if not data:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return data