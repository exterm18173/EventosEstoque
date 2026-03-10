from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.barcode import BarcodeLookupResponse
from app.services.barcode_service import BarcodeService

router = APIRouter(prefix="/barcode", tags=["Barcode"])
service = BarcodeService()


@router.get("/busca-por-nome", response_model=list[BarcodeLookupResponse])
def busca_por_nome(
    request: Request,
    q: str = Query(..., min_length=1, description="Nome do produto"),
    limit: int = Query(20, ge=1, le=100),
    local_id: int | None = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    try:
        return service.buscar_por_nome(
            db,
            request=request,
            q=q,
            limit=limit,
            local_id=local_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{codigo}", response_model=BarcodeLookupResponse)
def lookup(
    codigo: str,
    request: Request,
    local_id: int | None = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    try:
        return service.lookup(
            db,
            codigo,
            request=request,
            local_id=local_id,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )