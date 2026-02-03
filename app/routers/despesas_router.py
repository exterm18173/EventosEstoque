from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.despesas import DespesaCreate, DespesaUpdate, DespesaRead, DespesaImportResult
from app.schemas.despesas_relatorio import DespesaResumoResponse
from app.services.despesas_service import DespesasService

router = APIRouter(prefix="/despesas", tags=["Despesas"])
service = DespesasService()


@router.get("", response_model=list[DespesaRead])
def listar(
    evento_id: int | None = Query(default=None),
    categoria: str | None = Query(default=None),
    data_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(default=None, description="YYYY-MM-DD"),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(db, evento_id=evento_id, categoria=categoria, data_inicio=data_inicio, data_fim=data_fim, q=q)


@router.get("/{despesa_id}", response_model=DespesaRead)
def obter(despesa_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, despesa_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=DespesaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: DespesaCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{despesa_id}", response_model=DespesaRead)
def atualizar(despesa_id: int, payload: DespesaUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, despesa_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404 if "não encontrada" in str(e).lower() else 400, detail=str(e))


@router.delete("/{despesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(despesa_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, despesa_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/importar/csv", response_model=DespesaImportResult)
def importar_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        return service.importar_csv(db, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relatorio/resumo", response_model=DespesaResumoResponse)
def resumo(
    agrupamento: str = Query(..., description="periodo|categoria|evento"),
    inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    fim: str | None = Query(default=None, description="YYYY-MM-DD"),
    evento_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return service.resumo(db, agrupamento=agrupamento, inicio=inicio, fim=fim, evento_id=evento_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
