from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.orcamentos import (
    OrcamentoCreate,
    OrcamentoUpdate,
    OrcamentoRead,
    OrcamentoListItem,
)
from app.schemas.orcamento_itens import (
    OrcamentoItemCreate,
    OrcamentoItemUpdate,
    OrcamentoItemRead,
)
from app.schemas.orcamentos_convert import OrcamentoToAluguelRequest

from app.services.orcamentos_service import OrcamentoService
from app.schemas.alugueis import AluguelRead  # se existir (senão crie um)
# ou então retorne dict/AluguelRead do seu padrão


router = APIRouter(prefix="/orcamentos", tags=["Orçamentos"])
service = OrcamentoService()


@router.get("", response_model=list[OrcamentoListItem])
def listar(
    q: str | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    cliente_id: int | None = Query(default=None),
    evento_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        q=q,
        status=status_,
        cliente_id=cliente_id,
        evento_id=evento_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{orcamento_id}", response_model=OrcamentoRead)
def obter(orcamento_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, orcamento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=OrcamentoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: OrcamentoCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.put("/{orcamento_id}", response_model=OrcamentoRead)
def atualizar(orcamento_id: int, payload: OrcamentoUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, orcamento_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(orcamento_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, orcamento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------
# ITENS DO ORÇAMENTO
# --------------------

@router.get("/{orcamento_id}/itens", response_model=list[OrcamentoItemRead])
def listar_itens(orcamento_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_itens(db, orcamento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{orcamento_id}/itens", response_model=OrcamentoItemRead, status_code=status.HTTP_201_CREATED)
def adicionar_item(orcamento_id: int, payload: OrcamentoItemCreate, db: Session = Depends(get_db)):
    try:
        return service.add_item(db, orcamento_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{orcamento_id}/itens/{item_id}", response_model=OrcamentoItemRead)
def atualizar_item(
    orcamento_id: int,
    item_id: int,
    payload: OrcamentoItemUpdate,
    db: Session = Depends(get_db),
):
    try:
        return service.update_item(db, orcamento_id, item_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{orcamento_id}/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_item(orcamento_id: int, item_id: int, db: Session = Depends(get_db)):
    try:
        service.delete_item(db, orcamento_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------
# CONVERTER ORÇAMENTO -> ALUGUEL
# --------------------

@router.post("/{orcamento_id}/to-aluguel", response_model=AluguelRead)
def converter_para_aluguel(
    orcamento_id: int,
    payload: OrcamentoToAluguelRequest,
    db: Session = Depends(get_db),
):
    try:
        aluguel = service.to_aluguel(
            db,
            orcamento_id=orcamento_id,
            status_aluguel=payload.status_aluguel,
            copiar_datas=payload.copiar_datas,
            copiar_observacao=payload.copiar_observacao,
        )
        return aluguel
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
