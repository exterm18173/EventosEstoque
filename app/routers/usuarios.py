from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioRead
from app.services.usuarios_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])
service = UsuarioService()


@router.get("", response_model=list[UsuarioRead])
def listar(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.list(db, q=q)


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obter(usuario_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar(payload: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{usuario_id}", response_model=UsuarioRead)
def atualizar(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, usuario_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(usuario_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, usuario_id)
        return None
    except ValueError as e:
        # aqui vai cair o "use desativar..."
        raise HTTPException(status_code=400, detail=str(e))


# ✅ rota útil pro MVP: desativar/ativar (soft delete)
@router.post("/{usuario_id}/ativar", response_model=UsuarioRead)
def ativar(usuario_id: int, db: Session = Depends(get_db)):
    try:
        return service.update(db, usuario_id, UsuarioUpdate(ativo=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{usuario_id}/desativar", response_model=UsuarioRead)
def desativar(usuario_id: int, db: Session = Depends(get_db)):
    try:
        return service.update(db, usuario_id, UsuarioUpdate(ativo=False))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
