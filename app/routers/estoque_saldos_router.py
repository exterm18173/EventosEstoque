from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.estoque_saldos import EstoqueSaldoRead, EstoqueSaldoConsolidadoRead
from app.services.estoque_saldos_service import EstoqueSaldosService

router = APIRouter(prefix="/estoque/saldos", tags=["Estoque - Saldos"])
service = EstoqueSaldosService()


@router.get("", response_model=list[EstoqueSaldoRead])
def listar(
    local_id: int | None = Query(default=None),
    produto_id: int | None = Query(default=None),
    produto_base_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        local_id=local_id,
        produto_id=produto_id,
        produto_base_id=produto_base_id,
        q=q,
    )


@router.get("/consolidado", response_model=list[EstoqueSaldoConsolidadoRead])
def consolidado(local_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    return service.consolidado_produto_base(db, local_id=local_id)


@router.get("/{produto_id}", response_model=list[EstoqueSaldoRead])
def por_produto(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.by_produto(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
