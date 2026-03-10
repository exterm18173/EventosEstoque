from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fornecedor_produto_vinculo import (
    FornecedorProdutoVinculoCreate,
    FornecedorProdutoVinculoRead,
    FornecedorProdutoVinculoUpdate,
)
from app.services.fornecedor_produto_vinculo_service import FornecedorProdutoVinculoService

router = APIRouter(
    prefix="/fornecedor-produto-vinculos",
    tags=["Fiscal - Vínculos Fornecedor Produto"],
)

service = FornecedorProdutoVinculoService()


@router.get("", response_model=list[FornecedorProdutoVinculoRead])
def listar(
    fornecedor_cnpj: Optional[str] = Query(default=None),
    produto_id: Optional[int] = Query(default=None, gt=0),
    termo: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        fornecedor_cnpj=fornecedor_cnpj,
        produto_id=produto_id,
        termo=termo,
    )


@router.get("/{vinculo_id}", response_model=FornecedorProdutoVinculoRead)
def obter(
    vinculo_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.get(db, vinculo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=FornecedorProdutoVinculoRead, status_code=status.HTTP_201_CREATED)
def criar(
    payload: FornecedorProdutoVinculoCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=400, detail=msg)


@router.put("/{vinculo_id}", response_model=FornecedorProdutoVinculoRead)
def atualizar(
    vinculo_id: int,
    payload: FornecedorProdutoVinculoUpdate,
    db: Session = Depends(get_db),
):
    try:
        return service.update(db, vinculo_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.delete("/{vinculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    vinculo_id: int,
    db: Session = Depends(get_db),
):
    try:
        service.delete(db, vinculo_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))