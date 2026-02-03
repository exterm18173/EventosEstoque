from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.categorias_produto import (
    CategoriaProdutoCreate,
    CategoriaProdutoUpdate,
    CategoriaProdutoRead,
    CategoriaProdutoTreeNode,
)
from app.services.categorias_produto_service import CategoriaProdutoService

router = APIRouter(prefix="/categorias-produto", tags=["Categorias Produto"])
service = CategoriaProdutoService()


@router.get("", response_model=list[CategoriaProdutoRead])
def listar(
    tipo: str | None = Query(default=None),
    parent_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(db, tipo=tipo, parent_id=parent_id, q=q)


@router.get("/arvore", response_model=list[CategoriaProdutoTreeNode])
def arvore(tipo: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.tree(db, tipo=tipo)


@router.get("/{categoria_id}", response_model=CategoriaProdutoRead)
def obter(categoria_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, categoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CategoriaProdutoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: CategoriaProdutoCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{categoria_id}", response_model=CategoriaProdutoRead)
def atualizar(categoria_id: int, payload: CategoriaProdutoUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, categoria_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(categoria_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, categoria_id)
        return None
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)
