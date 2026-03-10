from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.certificado_fiscal import CertificadoFiscal
from app.schemas.certificado_fiscal import CertificadoFiscalSincronizacaoResponse
from app.schemas.nota_recebida import NotaRecebidaCreate
from app.schemas.nota_recebida_item import NotaRecebidaItemCreate
from app.services.certificado_fiscal_service import CertificadoFiscalService
from app.services.nota_recebida_service import NotaRecebidaService
from app.integrations.sefaz.distribuicao_dfe import DistribuicaoDfeClient
from app.integrations.xml.nfe_parser import parse_nfe_xml_file


class NotaSincronizacaoService:
    def __init__(self) -> None:
        self.cert_service = CertificadoFiscalService()
        self.nota_service = NotaRecebidaService()

    def sincronizar_certificado(
        self,
        db: Session,
        *,
        certificado_id: int,
    ) -> CertificadoFiscalSincronizacaoResponse:
        certificado = self.cert_service.get(db, certificado_id)
        senha = self.cert_service.get_plain_password(certificado)

        client = DistribuicaoDfeClient(
            certificado_path=certificado.arquivo_path,
            certificado_password=senha,
            ambiente=certificado.ambiente,
            cnpj=certificado.cnpj,
        )

        resultado = client.consultar_documentos(ultimo_nsu=certificado.ultimo_nsu)

        notas_novas = 0
        notas_atualizadas = 0

        for doc in resultado.get("documentos", []):
            xml_path = doc["xml_path"]

            parsed = parse_nfe_xml_file(xml_path)

            existente = self.nota_service.get_by_chave(db, parsed["chave_acesso"])
            if existente:
                notas_atualizadas += 1
                continue

            payload = NotaRecebidaCreate(
                certificado_fiscal_id=certificado.id,
                fornecedor_id=None,
                compra_id=None,
                chave_acesso=parsed["chave_acesso"],
                numero=parsed.get("numero"),
                serie=parsed.get("serie"),
                modelo=parsed.get("modelo"),
                fornecedor_nome=parsed["fornecedor_nome"],
                fornecedor_cnpj=parsed.get("fornecedor_cnpj"),
                natureza_operacao=parsed.get("natureza_operacao"),
                cfop_predominante=parsed.get("cfop_predominante"),
                data_emissao=parsed.get("data_emissao"),
                data_autorizacao=parsed.get("data_autorizacao"),
                valor_total=parsed.get("valor_total"),
                valor_produtos=parsed.get("valor_produtos"),
                valor_frete=parsed.get("valor_frete"),
                valor_desconto=parsed.get("valor_desconto"),
                valor_outros=parsed.get("valor_outros"),
                protocolo=parsed.get("protocolo"),
                nsu=doc.get("nsu"),
                status="nova",
                xml_path=xml_path,
                xml_hash=parsed.get("xml_hash"),
                observacao=None,
                importada_em=None,
                itens=[
                    NotaRecebidaItemCreate(
                        numero_item=item["numero_item"],
                        codigo_fornecedor=item.get("codigo_fornecedor"),
                        codigo_barras=item.get("codigo_barras"),
                        descricao=item["descricao"],
                        ncm=item.get("ncm"),
                        cfop=item.get("cfop"),
                        unidade_comercial=item.get("unidade_comercial"),
                        quantidade=item["quantidade"],
                        valor_unitario=item.get("valor_unitario"),
                        valor_total=item.get("valor_total"),
                        produto_id=None,
                        embalagem_id=None,
                        unidade_informada_id=None,
                        lote_id=None,
                        status_conciliacao="nao_analisado",
                        observacao=None,
                    )
                    for item in parsed["itens"]
                ],
            )
            self.nota_service.create(db, payload)
            notas_novas += 1

        self.cert_service.atualizar_sincronizacao(
            db,
            certificado,
            ultimo_nsu=resultado.get("ultimo_nsu"),
        )

        return CertificadoFiscalSincronizacaoResponse(
            certificado_id=certificado.id,
            notas_novas=notas_novas,
            notas_atualizadas=notas_atualizadas,
            ultimo_nsu=resultado.get("ultimo_nsu"),
            mensagem="Sincronização concluída com sucesso.",
        )