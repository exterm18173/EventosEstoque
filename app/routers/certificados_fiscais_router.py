from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.certificado_fiscal import (
    CertificadoFiscalCreate,
    CertificadoFiscalListItem,
    CertificadoFiscalRead,
    CertificadoFiscalSincronizacaoResponse,
    CertificadoFiscalTesteResponse,
    CertificadoFiscalUpdate,
)
from app.services.certificado_fiscal_service import CertificadoFiscalService
from app.services.nota_sincronizacao_service import NotaSincronizacaoService

router = APIRouter(prefix="/certificados-fiscais", tags=["Fiscal - Certificados"])

service = CertificadoFiscalService()
sincronizacao_service = NotaSincronizacaoService()


@router.get("", response_model=list[CertificadoFiscalListItem])
def listar(
    ativo: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(db, ativo=ativo)


@router.get("/{certificado_id}", response_model=CertificadoFiscalRead)
def obter(
    certificado_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.get(db, certificado_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CertificadoFiscalRead, status_code=status.HTTP_201_CREATED)
def criar(
    payload: CertificadoFiscalCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create(db, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=400, detail=msg)


@router.put("/{certificado_id}", response_model=CertificadoFiscalRead)
def atualizar(
    certificado_id: int,
    payload: CertificadoFiscalUpdate,
    db: Session = Depends(get_db),
):
    try:
        return service.update(db, certificado_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )


@router.delete("/{certificado_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    certificado_id: int,
    db: Session = Depends(get_db),
):
    try:
        service.delete(db, certificado_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{certificado_id}/testar", response_model=CertificadoFiscalTesteResponse)
def testar(
    certificado_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.testar(db, certificado_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{certificado_id}/sincronizar", response_model=CertificadoFiscalSincronizacaoResponse)
def sincronizar(
    certificado_id: int,
    db: Session = Depends(get_db),
):
    try:
        return sincronizacao_service.sincronizar_certificado(
            db,
            certificado_id=certificado_id,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrado" in msg.lower() else 400,
            detail=msg,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao sincronizar certificado: {str(e)}",
        )