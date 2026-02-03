from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.produtos_base import (
    ProdutoBaseCreate,
    ProdutoBaseUpdate,
    ProdutoBaseRead,
    EstoqueConsolidadoRead,
)
from app.services.produtos_base_service import ProdutoBaseService
from app.schemas.produtos import ProdutoRead  # será criado no próximo passo

router = APIRouter(prefix="/produtos-base", tags=["Produtos Base"])
service = ProdutoBaseService()


@router.get("", response_model=list[ProdutoBaseRead])
def listar(
    categoria_id: int | None = Query(default=None),
    ativo: bool | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(db, categoria_id=categoria_id, ativo=ativo, q=q)


@router.get("/{produto_base_id}", response_model=ProdutoBaseRead)
def obter(produto_base_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, produto_base_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ProdutoBaseRead, status_code=status.HTTP_201_CREATED)
def criar(payload: ProdutoBaseCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{produto_base_id}", response_model=ProdutoBaseRead)
def atualizar(produto_base_id: int, payload: ProdutoBaseUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, produto_base_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/{produto_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(produto_base_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, produto_base_id)
        return None
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.get("/{produto_base_id}/variacoes", response_model=list["ProdutoRead"])
def listar_variacoes(produto_base_id: int, db: Session = Depends(get_db)):
    try:
        return service.variacoes(db, produto_base_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{produto_base_id}/estoque-consolidado", response_model=EstoqueConsolidadoRead)
def estoque_consolidado(
    produto_base_id: int,
    local_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        total = service.estoque_consolidado(db, produto_base_id, local_id=local_id)
        return EstoqueConsolidadoRead(
            produto_base_id=produto_base_id,
            total_quantidade_base=total,
            local_id=local_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
