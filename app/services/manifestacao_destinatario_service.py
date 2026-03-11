from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.integrations.sefaz.distribuicao_dfe import DistribuicaoDfeClient
from app.models.nota_recebida import NotaRecebida
from app.services.certificado_fiscal_service import CertificadoFiscalService
from app.services.nota_recebida_service import NotaRecebidaService


@dataclass
class ManifestacaoDestinatarioResult:
    sucesso: bool
    chave: str
    tipo_manifestacao: str
    cstat: Optional[str] = None
    xmotivo: Optional[str] = None
    protocolo: Optional[str] = None
    xml_path: Optional[str] = None
    mensagem: Optional[str] = None


class ManifestacaoDestinatarioService:
    def __init__(self) -> None:
        self.cert_service = CertificadoFiscalService()
        self.nota_service = NotaRecebidaService()

    def manifestar_por_chave(
        self,
        db: Session,
        *,
        certificado_id: int,
        chave: str,
        uf_autor: str,
        tipo_manifestacao: str = DistribuicaoDfeClient.TP_EVENTO_CIENCIA,
        justificativa: Optional[str] = None,
    ) -> ManifestacaoDestinatarioResult:
        certificado = self.cert_service.get(db, certificado_id)
        senha = self.cert_service.get_plain_password(certificado)

        client = DistribuicaoDfeClient(
            certificado_path=certificado.arquivo_path,
            certificado_password=senha,
            ambiente=certificado.ambiente,
            cnpj=certificado.cnpj,
            uf_autor=uf_autor,
        )

        try:
            resultado = client.manifestar_nota(
                chave=chave,
                tipo_manifestacao=tipo_manifestacao,
                justificativa=justificativa,
            )

            self._atualizar_nota_se_existir(
                db,
                chave=chave,
                tipo_manifestacao=tipo_manifestacao,
                xmotivo=resultado.get("xmotivo"),
                protocolo=resultado.get("protocolo"),
            )

            return ManifestacaoDestinatarioResult(
                sucesso=bool(resultado.get("sucesso")),
                chave=resultado.get("chave", chave),
                tipo_manifestacao=resultado.get(
                    "tipo_manifestacao",
                    tipo_manifestacao,
                ),
                cstat=resultado.get("cstat"),
                xmotivo=resultado.get("xmotivo"),
                protocolo=resultado.get("protocolo"),
                xml_path=resultado.get("xml_path"),
                mensagem=resultado.get("xmotivo") or "Manifestação concluída.",
            )
        except Exception as e:
            return ManifestacaoDestinatarioResult(
                sucesso=False,
                chave=chave,
                tipo_manifestacao=tipo_manifestacao,
                mensagem=f"Erro ao manifestar nota: {str(e)}",
            )

    def manifestar_nota_recebida(
        self,
        db: Session,
        *,
        certificado_id: int,
        nota_id: int,
        uf_autor: str,
        tipo_manifestacao: str = DistribuicaoDfeClient.TP_EVENTO_CIENCIA,
        justificativa: Optional[str] = None,
    ) -> ManifestacaoDestinatarioResult:
        nota = self.nota_service.get(db, nota_id)

        return self.manifestar_por_chave(
            db,
            certificado_id=certificado_id,
            chave=nota.chave_acesso,
            uf_autor=uf_autor,
            tipo_manifestacao=tipo_manifestacao,
            justificativa=justificativa,
        )

    def manifestar_e_tentar_baixar_xml(
        self,
        db: Session,
        *,
        certificado_id: int,
        chave: str,
        uf_autor: str,
        tipo_manifestacao: str = DistribuicaoDfeClient.TP_EVENTO_CIENCIA,
        justificativa: Optional[str] = None,
    ) -> dict:
        certificado = self.cert_service.get(db, certificado_id)
        senha = self.cert_service.get_plain_password(certificado)

        client = DistribuicaoDfeClient(
            certificado_path=certificado.arquivo_path,
            certificado_password=senha,
            ambiente=certificado.ambiente,
            cnpj=certificado.cnpj,
            uf_autor=uf_autor,
        )

        manifestacao = self.manifestar_por_chave(
            db,
            certificado_id=certificado_id,
            chave=chave,
            uf_autor=uf_autor,
            tipo_manifestacao=tipo_manifestacao,
            justificativa=justificativa,
        )

        if not manifestacao.sucesso:
            return {
                "manifestacao": manifestacao.__dict__,
                "download_xml": None,
                "mensagem": manifestacao.mensagem or "Falha na manifestação.",
            }

        try:
            consulta = client.consultar_documentos()
            documentos = consulta.get("documentos", [])

            documento_encontrado = None
            for doc in documentos:
                xml_path = doc.get("xml_path")
                if not xml_path:
                    continue

                nota = self.nota_service.get_by_chave(db, chave)
                if nota and nota.xml_path == xml_path:
                    documento_encontrado = doc
                    break

            return {
                "manifestacao": manifestacao.__dict__,
                "download_xml": documento_encontrado,
                "mensagem": (
                    "Manifestação concluída e consulta realizada novamente com sucesso."
                ),
            }
        except Exception as e:
            return {
                "manifestacao": manifestacao.__dict__,
                "download_xml": None,
                "mensagem": (
                    f"Manifestação concluída, mas houve erro ao tentar consultar o XML novamente: {str(e)}"
                ),
            }

    def _atualizar_nota_se_existir(
        self,
        db: Session,
        *,
        chave: str,
        tipo_manifestacao: str,
        xmotivo: Optional[str],
        protocolo: Optional[str],
    ) -> None:
        nota: Optional[NotaRecebida] = self.nota_service.get_by_chave(db, chave)
        if not nota:
            return

        observacoes = []

        if nota.observacao:
            observacoes.append(nota.observacao)

        observacoes.append(
            f"Manifestação enviada: {self._descricao_manifestacao(tipo_manifestacao)}"
        )

        if xmotivo:
            observacoes.append(f"Retorno SEFAZ: {xmotivo}")

        if protocolo:
            observacoes.append(f"Protocolo: {protocolo}")

        nota.observacao = " | ".join(observacoes)

        # status sugerido para controle interno
        if tipo_manifestacao == DistribuicaoDfeClient.TP_EVENTO_CIENCIA:
            nota.status = "manifestada_ciencia"
        elif tipo_manifestacao == DistribuicaoDfeClient.TP_EVENTO_CONFIRMACAO:
            nota.status = "manifestada_confirmacao"
        elif tipo_manifestacao == DistribuicaoDfeClient.TP_EVENTO_DESCONHECIMENTO:
            nota.status = "manifestada_desconhecimento"
        elif tipo_manifestacao == DistribuicaoDfeClient.TP_EVENTO_NAO_REALIZADA:
            nota.status = "manifestada_nao_realizada"

        db.commit()

    def _descricao_manifestacao(self, tipo_manifestacao: str) -> str:
        mapa = {
            DistribuicaoDfeClient.TP_EVENTO_CIENCIA: "Ciência da operação",
            DistribuicaoDfeClient.TP_EVENTO_CONFIRMACAO: "Confirmação da operação",
            DistribuicaoDfeClient.TP_EVENTO_DESCONHECIMENTO: "Desconhecimento da operação",
            DistribuicaoDfeClient.TP_EVENTO_NAO_REALIZADA: "Operação não realizada",
        }
        return mapa.get(tipo_manifestacao, tipo_manifestacao)