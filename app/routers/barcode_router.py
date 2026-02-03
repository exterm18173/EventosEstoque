from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.barcode import BarcodeLookupResponse
from app.services.barcode_service import BarcodeService

router = APIRouter(prefix="/barcode", tags=["Barcode"])
service = BarcodeService()


@router.get("/{codigo}", response_model=BarcodeLookupResponse)
def lookup(codigo: str, db: Session = Depends(get_db)):
    try:
        return service.lookup(db, codigo)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)
