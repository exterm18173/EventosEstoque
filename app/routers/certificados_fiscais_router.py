from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.certificado_fiscal import (
    CertificadoFiscalCreate,
    CertificadoFiscalListItem,
    CertificadoFiscalRead,
    CertificadoFiscalSincronizacaoResponse,
    CertificadoFiscalTesteResponse,
    CertificadoFiscalUpdate,
    CertificadoFiscalUploadResponse,
)
from app.services.certificado_fiscal_service import CertificadoFiscalService
from app.services.nota_sincronizacao_service import NotaSincronizacaoService

router = APIRouter(prefix="/certificados-fiscais", tags=["Fiscal - Certificados"])

service = CertificadoFiscalService()
sincronizacao_service = NotaSincronizacaoService()

UPLOAD_DIR = Path("storage/certificados")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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


@router.post("/upload", response_model=CertificadoFiscalUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_certificado(
    file: UploadFile = File(...),
):
    try:
        nome_original = file.filename or "certificado.pfx"
        ext = Path(nome_original).suffix.lower()

        if ext not in {".pfx", ".p12"}:
            raise HTTPException(
                status_code=400,
                detail="Envie um arquivo .pfx ou .p12.",
            )

        nome_gerado = f"{uuid.uuid4().hex}{ext}"
        destino = UPLOAD_DIR / nome_gerado

        with destino.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        tamanho = destino.stat().st_size

        return CertificadoFiscalUploadResponse(
            arquivo_path=str(destino),
            nome_original=nome_original,
            tamanho_bytes=tamanho,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar arquivo do certificado: {str(e)}",
        )


@router.post("", response_model=CertificadoFiscalRead, status_code=status.HTTP_201_CREATED)
def criar(
    payload: CertificadoFiscalCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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