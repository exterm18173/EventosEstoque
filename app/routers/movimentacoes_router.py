from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.movimentacoes_crud import (
    MovimentacaoCreate,
    MovimentacaoRead,
    MovimentacaoEstornoResponse,
)
from app.services.movimentacoes_service import MovimentacoesService

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])
service = MovimentacoesService()


# =========================
# LISTAR
# =========================
@router.get("", response_model=list[MovimentacaoRead])
def listar(
    produto_id: Optional[int] = Query(default=None, gt=0),
    evento_id: Optional[int] = Query(default=None, gt=0),
    aluguel_id: Optional[int] = Query(default=None, gt=0),
    setor_consumo_id: Optional[int] = Query(default=None, gt=0),
    tipo: Optional[str] = Query(default=None),
    origem: Optional[str] = Query(default=None),
    local_id: Optional[int] = Query(default=None, gt=0),
    data_inicio: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    data_fim: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        produto_id=produto_id,
        evento_id=evento_id,
        aluguel_id=aluguel_id,
        setor_consumo_id=setor_consumo_id,
        tipo=tipo,
        origem=origem,
        local_id=local_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


# =========================
# OBTER POR ID
# =========================
@router.get("/{mov_id}", response_model=MovimentacaoRead)
def obter(
    mov_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.get(db, mov_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================
# CRIAR (1 item)
# =========================
@router.post("", response_model=MovimentacaoRead, status_code=status.HTTP_201_CREATED)
def criar(
    payload: MovimentacaoCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


# =========================
# CAIXA (BATCH)
# =========================
@router.post(
    "/caixa",
    response_model=list[MovimentacaoRead],
    status_code=status.HTTP_201_CREATED,
)
def criar_caixa(
    payload: List[MovimentacaoCreate] = Body(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Fluxo "caixa de supermercado":
    - frontend monta uma lista de MovimentacaoCreate
    - backend salva tudo em lote (ou tudo ou nada)
    """
    try:
        return service.create_batch(db, payload)

    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao criar movimentações em lote: {str(e)}",
        )


# =========================
# ESTORNAR
# =========================
@router.post("/{mov_id}/estornar", response_model=MovimentacaoEstornoResponse)
def estornar(
    mov_id: int,
    usuario_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    try:
        estorno = service.estornar(db, mov_id, usuario_id=usuario_id)
        return MovimentacaoEstornoResponse(
            movimentacao_original_id=mov_id,
            movimentacao_estorno_id=estorno.id,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.post(
    "/lote",
    response_model=list[MovimentacaoRead],
    status_code=status.HTTP_201_CREATED,
)
def criar_lote(
    payload: List[MovimentacaoCreate] = Body(...),
    db: Session = Depends(get_db),
):
    try:
        return service.create_batch(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )