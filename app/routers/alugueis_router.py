from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.alugueis import (
    AluguelCreate, AluguelUpdate, AluguelRead,
    AluguelSaidaRequest, AluguelDevolucaoRequest, AluguelAcaoResponse
)
from app.schemas.aluguel_itens import AluguelItemCreate, AluguelItemUpdate, AluguelItemRead
from app.services.alugueis_service import AlugueisService
from app.services.aluguel_itens_service import AluguelItensService
from app.services.aluguel_acoes_service import AluguelAcoesService
from fastapi import File, UploadFile, Form
router = APIRouter(prefix="/aluguels", tags=["Aluguéis"])
service = AlugueisService()
itens_service = AluguelItensService()
acoes_service = AluguelAcoesService()


@router.get("", response_model=list[AluguelRead])
def listar(
    cliente_id: int | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    return service.list(db, cliente_id=cliente_id, status=status_)


@router.get("/{aluguel_id}", response_model=AluguelRead)
def obter(aluguel_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, aluguel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=AluguelRead, status_code=status.HTTP_201_CREATED)
def criar(payload: AluguelCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{aluguel_id}", response_model=AluguelRead)
def atualizar(aluguel_id: int, payload: AluguelUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, aluguel_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404 if "não encontrado" in str(e).lower() else 400, detail=str(e))


@router.delete("/{aluguel_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(aluguel_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, aluguel_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------- itens --------
@router.get("/{aluguel_id}/itens", response_model=list[AluguelItemRead])
def listar_itens(aluguel_id: int, db: Session = Depends(get_db)):
    try:
        return itens_service.list_by_aluguel(db, aluguel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{aluguel_id}/itens", response_model=AluguelItemRead, status_code=status.HTTP_201_CREATED)
def criar_item(aluguel_id: int, payload: AluguelItemCreate, db: Session = Depends(get_db)):
    try:
        return itens_service.create(db, aluguel_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/itens/{item_id}", response_model=AluguelItemRead)
def atualizar_item(item_id: int, payload: AluguelItemUpdate, db: Session = Depends(get_db)):
    try:
        return itens_service.update(db, item_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404 if "não encontrado" in str(e).lower() else 400, detail=str(e))


@router.delete("/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_item(item_id: int, db: Session = Depends(get_db)):
    try:
        itens_service.delete(db, item_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------- ações --------
@router.post("/{aluguel_id}/saida", response_model=AluguelAcaoResponse)
def saida(aluguel_id: int, payload: AluguelSaidaRequest, db: Session = Depends(get_db)):
    try:
        criadas = acoes_service.saida(
            db,
            aluguel_id,
            local_origem_id=payload.local_origem_id,
            usuario_id=payload.usuario_id,
            origem=payload.origem,
            observacao=payload.observacao,
        )
        aluguel = service.get(db, aluguel_id)
        return AluguelAcaoResponse(aluguel_id=aluguel_id, status=aluguel.status, movimentacoes_criadas=criadas)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{aluguel_id}/devolucao", response_model=AluguelAcaoResponse)
def devolucao(aluguel_id: int, payload: AluguelDevolucaoRequest, db: Session = Depends(get_db)):
    try:
        criadas = acoes_service.devolucao(
            db,
            aluguel_id,
            local_destino_id=payload.local_destino_id,
            usuario_id=payload.usuario_id,
            origem=payload.origem,
            observacao=payload.observacao,
        )
        aluguel = service.get(db, aluguel_id)
        return AluguelAcaoResponse(aluguel_id=aluguel_id, status=aluguel.status, movimentacoes_criadas=criadas)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/{aluguel_id}/itens/{item_id}/devolver", response_model=AluguelAcaoResponse)
def devolver_item(
    aluguel_id: int,
    item_id: int,
    local_destino_id: int = Form(...),
    usuario_id: int = Form(...),
    quantidade_devolver_base: float = Form(...),
    lote_id: int | None = Form(None),  # <-- novo
    origem: str = Form("aluguel"),
    observacao: str | None = Form(None),
    foto: UploadFile = File(...),  # OBRIGATÓRIA
    db: Session = Depends(get_db),
):
    try:
        criadas = acoes_service.devolver_item_com_foto(
            db,
            aluguel_id=aluguel_id,
            item_id=item_id,
            local_destino_id=local_destino_id,
            usuario_id=usuario_id,
            quantidade_devolver_base=quantidade_devolver_base,
            lote_id=lote_id,
            origem=origem,
            observacao=observacao,
            foto=foto,
        )
        aluguel = service.get(db, aluguel_id)
        return AluguelAcaoResponse(
            aluguel_id=aluguel_id,
            status=aluguel.status,
            movimentacoes_criadas=criadas,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))