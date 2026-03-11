from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.manifestacao_destinatario import (
    ManifestacaoComDownloadResponse,
    ManifestacaoDestinatarioPayload,
    ManifestacaoDestinatarioResponse,
)
from app.schemas.nota_recebida import (
    NotaRecebidaDetalhe,
    NotaRecebidaListItem,
    NotaRecebidaRead,
    NotaRecebidaResumoImportacao,
    NotaRecebidaStatusUpdate,
)
from app.services.manifestacao_destinatario_service import (
    ManifestacaoDestinatarioService,
)
from app.services.nota_conciliacao_service import NotaConciliacaoService
from app.services.nota_recebida_service import NotaRecebidaService

router = APIRouter(prefix="/notas-recebidas", tags=["Fiscal - Notas Recebidas"])

service = NotaRecebidaService()
conciliacao_service = NotaConciliacaoService()
manifestacao_service = ManifestacaoDestinatarioService()


@router.get("", response_model=list[NotaRecebidaListItem])
def listar(
    certificado_fiscal_id: Optional[int] = Query(default=None, gt=0),
    fornecedor_id: Optional[int] = Query(default=None, gt=0),
    fornecedor_nome: Optional[str] = Query(default=None),
    fornecedor_cnpj: Optional[str] = Query(default=None),
    chave_acesso: Optional[str] = Query(default=None),
    numero: Optional[str] = Query(default=None),
    serie: Optional[str] = Query(default=None),
    modelo: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list(
        db,
        certificado_fiscal_id=certificado_fiscal_id,
        fornecedor_id=fornecedor_id,
        fornecedor_nome=fornecedor_nome,
        fornecedor_cnpj=fornecedor_cnpj,
        chave_acesso=chave_acesso,
        numero=numero,
        serie=serie,
        modelo=modelo,
        status=status,
    )


@router.get("/{nota_id}", response_model=NotaRecebidaDetalhe)
def obter(
    nota_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.get(db, nota_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{nota_id}/xml")
def baixar_xml(
    nota_id: int,
    db: Session = Depends(get_db),
):
    try:
        nota = service.get(db, nota_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not nota.xml_path:
        raise HTTPException(status_code=404, detail="XML não disponível para esta nota.")

    return FileResponse(
        path=nota.xml_path,
        filename=f"{nota.chave_acesso}.xml",
        media_type="application/xml",
    )


@router.post("/{nota_id}/status", response_model=NotaRecebidaRead)
def atualizar_status(
    nota_id: int,
    payload: NotaRecebidaStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        return service.update_status(db, nota_id, payload)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/{nota_id}/ignorar", response_model=NotaRecebidaRead)
def ignorar(
    nota_id: int,
    observacao: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return service.ignorar(db, nota_id, observacao=observacao)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/{nota_id}/auto-conciliar", response_model=NotaRecebidaResumoImportacao)
def auto_conciliar(
    nota_id: int,
    db: Session = Depends(get_db),
):
    try:
        conciliacao_service.auto_conciliar_nota(db, nota_id)

        nota = service.get(db, nota_id)
        resumo = conciliacao_service.resumo_nota(db, nota_id)

        return NotaRecebidaResumoImportacao(
            nota_recebida_id=nota.id,
            compra_id=nota.compra_id,
            total_itens=resumo["total_itens"],
            pendentes=resumo["pendentes"],
            vinculados=resumo["vinculados"],
            novos_produtos=resumo["novos_produtos"],
            ignorados=resumo["ignorados"],
            conflitos=resumo["conflitos"],
            valor_total=nota.valor_total,
            pronta_para_importar=(resumo["pendentes"] == 0 and resumo["conflitos"] == 0),
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )


@router.post("/{nota_id}/manifestar", response_model=ManifestacaoDestinatarioResponse)
def manifestar(
    nota_id: int,
    payload: ManifestacaoDestinatarioPayload,
    db: Session = Depends(get_db),
):
    try:
        resultado = manifestacao_service.manifestar_nota_recebida(
            db,
            certificado_id=payload.certificado_fiscal_id,
            nota_id=nota_id,
            uf_autor=payload.uf_autor,
            tipo_manifestacao=payload.tipo_manifestacao,
            justificativa=payload.justificativa,
        )

        return ManifestacaoDestinatarioResponse(
            sucesso=resultado.sucesso,
            chave=resultado.chave,
            tipo_manifestacao=resultado.tipo_manifestacao,
            cstat=resultado.cstat,
            xmotivo=resultado.xmotivo,
            protocolo=resultado.protocolo,
            xml_path=resultado.xml_path,
            mensagem=resultado.mensagem,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao manifestar nota: {str(e)}",
        )


@router.post(
    "/{nota_id}/manifestar-e-baixar",
    response_model=ManifestacaoComDownloadResponse,
)
def manifestar_e_baixar(
    nota_id: int,
    payload: ManifestacaoDestinatarioPayload,
    db: Session = Depends(get_db),
):
    try:
        nota = service.get(db, nota_id)

        resultado = manifestacao_service.manifestar_e_tentar_baixar_xml(
            db,
            certificado_id=payload.certificado_fiscal_id,
            chave=nota.chave_acesso,
            uf_autor=payload.uf_autor,
            tipo_manifestacao=payload.tipo_manifestacao,
            justificativa=payload.justificativa,
        )

        manifestacao = resultado["manifestacao"]

        return ManifestacaoComDownloadResponse(
            manifestacao=ManifestacaoDestinatarioResponse(
                sucesso=manifestacao["sucesso"],
                chave=manifestacao["chave"],
                tipo_manifestacao=manifestacao["tipo_manifestacao"],
                cstat=manifestacao.get("cstat"),
                xmotivo=manifestacao.get("xmotivo"),
                protocolo=manifestacao.get("protocolo"),
                xml_path=manifestacao.get("xml_path"),
                mensagem=manifestacao.get("mensagem"),
            ),
            download_xml=resultado.get("download_xml"),
            mensagem=resultado.get("mensagem", "Operação concluída."),
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=404 if "não encontrada" in msg.lower() else 400,
            detail=msg,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao manifestar/baixar XML: {str(e)}",
        )