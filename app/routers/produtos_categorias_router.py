from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.produtos_categorias import ProdutoCategoriaRead
from app.services.produtos_categorias_service import ProdutoCategoriaService

router = APIRouter(tags=["Produtos - Categorias"])
service = ProdutoCategoriaService()


@router.get("/produtos/{produto_id}/categorias", response_model=list[ProdutoCategoriaRead])
def listar(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.list(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/produtos/{produto_id}/categorias/{categoria_id}",
    response_model=ProdutoCategoriaRead,
    status_code=status.HTTP_201_CREATED,
)
def adicionar(produto_id: int, categoria_id: int, db: Session = Depends(get_db)):
    try:
        return service.add(db, produto_id, categoria_id)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404, detail=msg)


@router.delete("/produtos/{produto_id}/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(produto_id: int, categoria_id: int, db: Session = Depends(get_db)):
    try:
        service.remove(db, produto_id, categoria_id)
        return None
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)
