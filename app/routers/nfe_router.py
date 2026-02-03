from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.nfe import NfeDocumentoListItem, NfeDocumentoRead, NfeItemRead, NfeItemUpdate
from app.services.nfe_service import NfeService

router = APIRouter(prefix="/nfe", tags=["NF-e"])
service = NfeService()


@router.get("/documentos", response_model=list[NfeDocumentoListItem])
def listar_documentos(db: Session = Depends(get_db)):
    return service.list_documentos(db)


@router.get("/documentos/{doc_id}", response_model=NfeDocumentoRead)
def obter_documento(doc_id: int, db: Session = Depends(get_db)):
    try:
        return service.get_documento(db, doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/documentos/upload", response_model=NfeDocumentoRead)
def upload_xml(
    usuario_id: int | None = Query(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        return service.upload_xml(db, usuario_id=usuario_id, file=file)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=400, detail=msg)


@router.get("/documentos/{doc_id}/download")
def download_xml(doc_id: int, db: Session = Depends(get_db)):
    try:
        doc = service.get_documento(db, doc_id)
        if not doc.xml_path:
            raise ValueError("Documento sem xml_path.")
        return FileResponse(
            path=doc.xml_path,
            media_type="application/xml",
            filename=f"{doc.chave_acesso}.xml",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/documentos/{doc_id}/itens", response_model=list[NfeItemRead])
def listar_itens(doc_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_itens(db, doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/itens/{item_id}", response_model=NfeItemRead)
def atualizar_item(item_id: int, payload: NfeItemUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_item(
            db,
            item_id,
            produto_id_sugerido=payload.produto_id_sugerido,
            embalagem_id_sugerida=payload.embalagem_id_sugerida,
            fator_sugerido=payload.fator_sugerido,
            status=payload.status,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=404 if "não encontrado" in msg.lower() else 400, detail=msg)
