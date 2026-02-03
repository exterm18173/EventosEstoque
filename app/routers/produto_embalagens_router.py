from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.produto_embalagens import EmbalagemCreate, EmbalagemUpdate, EmbalagemRead
from app.services.produto_embalagens_service import EmbalagemService

router = APIRouter(tags=["Embalagens"])
service = EmbalagemService()


@router.get("/produtos/{produto_id}/embalagens", response_model=list[EmbalagemRead])
def listar_embalagens(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_by_produto(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/produtos/{produto_id}/embalagens",
    response_model=EmbalagemRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_embalagem(produto_id: int, payload: EmbalagemCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, produto_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "produto não encontrado" in msg.lower() else 400, detail=msg)


@router.put("/embalagens/{embalagem_id}", response_model=EmbalagemRead)
def atualizar_embalagem(embalagem_id: int, payload: EmbalagemUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, embalagem_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrada" in msg.lower() else 400, detail=msg)


@router.delete("/embalagens/{embalagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_embalagem(embalagem_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, embalagem_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/embalagens/{embalagem_id}/definir-principal", response_model=EmbalagemRead)
def definir_principal(embalagem_id: int, db: Session = Depends(get_db)):
    try:
        return service.definir_principal(db, embalagem_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
