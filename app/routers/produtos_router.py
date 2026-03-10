from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.produtos import ProdutoCreate, ProdutoUpdate, ProdutoRead, ProdutoListItem
from app.schemas.estoque import ProdutoSaldoRead
from app.schemas.movimentacoes import MovimentacaoListItem

from app.services.produtos_service import ProdutoService

# schemas que já existem nos models, mas endpoints de leitura só (vamos criar nos próximos passos)
from app.schemas.produto_embalagens import EmbalagemRead  # próximo passo
from app.schemas.codigos_barras import CodigoBarrasRead   # próximo passo
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
router = APIRouter(prefix="/produtos", tags=["Produtos"])
service = ProdutoService()


@router.get("", response_model=list[ProdutoListItem])
def listar(
    produto_base_id: int | None = Query(default=None),
    marca_id: int | None = Query(default=None),
    ativo: bool | None = Query(default=None),
    eh_alugavel: bool | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        produto_base_id=produto_base_id,
        marca_id=marca_id,
        ativo=ativo,
        eh_alugavel=eh_alugavel,
        q=q,
    )


@router.get("/{produto_id}", response_model=ProdutoRead)
def obter(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ProdutoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: ProdutoCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{produto_id}", response_model=ProdutoRead)
def atualizar(produto_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, produto_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(produto_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, produto_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{produto_id}/saldos", response_model=list[ProdutoSaldoRead])
def saldos(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.saldos(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{produto_id}/movimentacoes", response_model=list[MovimentacaoListItem])
def movimentacoes(
    produto_id: int,
    data_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(default=None, description="YYYY-MM-DD"),
    tipo: str | None = Query(default=None),
    origem: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return service.movimentacoes(
            db,
            produto_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipo=tipo,
            origem=origem,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{produto_id}/embalagens", response_model=list[EmbalagemRead])
def embalagens(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.embalagens(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{produto_id}/codigos-barras", response_model=list[CodigoBarrasRead])
def codigos_barras(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.codigos_barras(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.post("/{produto_id}/foto", response_model=ProdutoRead)
def upload_foto(produto_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        return service.upload_foto(db, produto_id, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{produto_id}/foto")
def download_foto(produto_id: int, db: Session = Depends(get_db)):
    try:
        p = service.get(db, produto_id)
        if not p.foto_path:
            raise ValueError("Produto sem foto.")
        return FileResponse(
            path=p.foto_path,
            media_type=p.foto_mime or "application/octet-stream",
            filename=p.foto_nome_original or "foto",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{produto_id}/foto", response_model=ProdutoRead)
def excluir_foto(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.delete_foto(db, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))