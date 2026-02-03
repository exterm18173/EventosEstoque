from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.lotes import LoteCreate, LoteUpdate, LoteRead
from app.services.lotes_service import LoteService

router = APIRouter(tags=["Lotes"])
service = LoteService()


@router.get("/lotes", response_model=list[LoteRead])
def listar(
    produto_id: int | None = Query(default=None),
    local_id: int | None = Query(default=None),
    validade_ate: str | None = Query(default=None, description="YYYY-MM-DD"),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(db, produto_id=produto_id, local_id=local_id, validade_ate=validade_ate, q=q)


@router.get("/lotes/{lote_id}", response_model=LoteRead)
def obter(lote_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, lote_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/lotes", response_model=LoteRead, status_code=status.HTTP_201_CREATED)
def criar(payload: LoteCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.put("/lotes/{lote_id}", response_model=LoteRead)
def atualizar(lote_id: int, payload: LoteUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, lote_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/lotes/{lote_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(lote_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, lote_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/produtos/{produto_id}/lotes", response_model=list[LoteRead])
def listar_por_produto(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_by_produto(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
