from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.movimentacoes_crud import MovimentacaoCreate, MovimentacaoRead, MovimentacaoEstornoResponse
from app.services.movimentacoes_service import MovimentacoesService

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])
service = MovimentacoesService()


@router.get("", response_model=list[MovimentacaoRead])
def listar(
    produto_id: int | None = Query(default=None),
    evento_id: int | None = Query(default=None),
    aluguel_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None),
    origem: str | None = Query(default=None),
    local_id: int | None = Query(default=None),
    data_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        produto_id=produto_id,
        evento_id=evento_id,
        aluguel_id=aluguel_id,
        tipo=tipo,
        origem=origem,
        local_id=local_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.get("/{mov_id}", response_model=MovimentacaoRead)
def obter(mov_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, mov_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=MovimentacaoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: MovimentacaoCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.post("/{mov_id}/estornar", response_model=MovimentacaoEstornoResponse)
def estornar(mov_id: int, usuario_id: int, db: Session = Depends(get_db)):
    try:
        estorno = service.estornar(db, mov_id, usuario_id=usuario_id)
        return MovimentacaoEstornoResponse(
            movimentacao_original_id=mov_id,
            movimentacao_estorno_id=estorno.id,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)
