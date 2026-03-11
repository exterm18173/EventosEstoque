from __future__ import annotations

import base64
import gzip
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

from pynfe.processamento.comunicacao import ComunicacaoSefaz


class DistribuicaoDfeClient:
    TP_EVENTO_CIENCIA = "210210"
    TP_EVENTO_CONFIRMACAO = "210200"
    TP_EVENTO_DESCONHECIMENTO = "210220"
    TP_EVENTO_NAO_REALIZADA = "210240"

    UFS_VALIDAS = {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    }

    def __init__(
        self,
        *,
        certificado_path: str,
        certificado_password: str,
        ambiente: str,
        cnpj: str,
        uf_autor: str,
        storage_dir: str | Path = "storage/nfe_distribuicao",
        auto_manifestar_resumos: bool = False,
        tipo_manifestacao: str = TP_EVENTO_CIENCIA,
        justificativa_operacao_nao_realizada: Optional[str] = None,
    ):
        self.certificado_path = str(certificado_path)
        self.certificado_password = certificado_password
        self.ambiente = ambiente
        self.cnpj = self._only_digits(cnpj)
        self.uf_autor = self._normalize_uf(uf_autor)
        self.storage_dir = Path(storage_dir) / self.cnpj
        self.auto_manifestar_resumos = auto_manifestar_resumos
        self.tipo_manifestacao = tipo_manifestacao
        self.justificativa_operacao_nao_realizada = justificativa_operacao_nao_realizada

        self.storage_dir.mkdir(parents=True, exist_ok=True)

        cert_path = Path(self.certificado_path)
        if not cert_path.exists():
            raise ValueError("Arquivo do certificado não encontrado.")

        if cert_path.suffix.lower() not in {".pfx", ".p12"}:
            raise ValueError("Certificado inválido. Use .pfx ou .p12.")

        if len(self.cnpj) != 14:
            raise ValueError("CNPJ inválido para distribuição DF-e.")

    def consultar_documentos(self, *, ultimo_nsu: str | None = None) -> dict:
        con = self._build_comunicacao()
        nsu_inicial = self._normalize_nsu(ultimo_nsu)

        resposta = con.consulta_distribuicao(
            cnpj=self.cnpj,
            nsu=nsu_inicial,
        )

        xml_text = self._response_to_text(resposta)
        raw_response_path = self._save_raw_response(xml_text)

        ret_root = self._extract_ret_dist(xml_text)

        cstat = self._find_text(ret_root, "cStat")
        xmotivo = self._find_text(ret_root, "xMotivo")
        ult_nsu = self._find_text(ret_root, "ultNSU")
        max_nsu = self._find_text(ret_root, "maxNSU")

        documentos: list[dict[str, Any]] = []
        resumos: list[dict[str, Any]] = []
        eventos: list[dict[str, Any]] = []
        documentos_todos: list[dict[str, Any]] = []

        # Se não vier documento localizado, retorna diagnóstico completo
        if cstat != "138":
            return {
                "cstat": cstat,
                "xmotivo": xmotivo,
                "ultimo_nsu": ult_nsu,
                "max_nsu": max_nsu,
                "documentos": documentos,
                "resumos": resumos,
                "eventos": eventos,
                "documentos_todos": documentos_todos,
                "raw_response_path": str(raw_response_path),
            }

        for doc_zip in self._findall_local(ret_root, "docZip"):
            nsu = (doc_zip.attrib.get("NSU") or "").strip()
            schema = (doc_zip.attrib.get("schema") or "").strip()
            xml_doc = self._decode_doczip(doc_zip.text or "")

            xml_path = self._save_document_xml(
                xml_content=xml_doc,
                nsu=nsu,
                schema=schema,
            )

            item = {
                "nsu": nsu,
                "schema": schema,
                "xml_path": str(xml_path),
                "tipo": self._infer_tipo_documento(
                    schema=schema,
                    xml_content=xml_doc,
                ),
            }

            documentos_todos.append(item)

            if item["tipo"] == "nfe_proc":
                documentos.append(item)
            elif item["tipo"] == "resumo_nfe":
                resumos.append(item)
            else:
                eventos.append(item)

        # deixei a base pronta, mas sem manifestação automática por enquanto
        # para não complicar o fluxo até a distribuição funcionar redonda
        return {
            "cstat": cstat,
            "xmotivo": xmotivo,
            "ultimo_nsu": ult_nsu,
            "max_nsu": max_nsu,
            "documentos": documentos,
            "resumos": resumos,
            "eventos": eventos,
            "documentos_todos": documentos_todos,
            "raw_response_path": str(raw_response_path),
        }
    def manifestar_nota(
        self,
        *,
        chave: str,
        tipo_manifestacao: str = TP_EVENTO_CIENCIA,
        justificativa: Optional[str] = None,
        sequencia_evento: int = 1,
    ) -> dict:
        from datetime import datetime, timezone
        from lxml import etree

        chave = self._only_digits(chave)
        if len(chave) != 44:
            raise ValueError("Chave de acesso inválida para manifestação.")

        if tipo_manifestacao not in {
            self.TP_EVENTO_CIENCIA,
            self.TP_EVENTO_CONFIRMACAO,
            self.TP_EVENTO_DESCONHECIMENTO,
            self.TP_EVENTO_NAO_REALIZADA,
        }:
            raise ValueError("Tipo de manifestação inválido.")

        if tipo_manifestacao == self.TP_EVENTO_NAO_REALIZADA:
            if not justificativa or len(justificativa.strip()) < 15:
                raise ValueError(
                    "Para operação não realizada, informe justificativa com pelo menos 15 caracteres."
                )

        ns = "http://www.portalfiscal.inf.br/nfe"
        evento = etree.Element("evento", versao="1.00", xmlns=ns)
        inf = etree.SubElement(
            evento,
            "infEvento",
            Id=f"ID{tipo_manifestacao}{chave}{str(sequencia_evento).zfill(2)}",
        )

        etree.SubElement(inf, "cOrgao").text = "91"
        etree.SubElement(inf, "tpAmb").text = "2" if self._is_homologacao(self.ambiente) else "1"
        etree.SubElement(inf, "CNPJ").text = self.cnpj
        etree.SubElement(inf, "chNFe").text = chave
        etree.SubElement(inf, "dhEvento").text = (
            datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        )
        etree.SubElement(inf, "tpEvento").text = tipo_manifestacao
        etree.SubElement(inf, "nSeqEvento").text = str(sequencia_evento)
        etree.SubElement(inf, "verEvento").text = "1.00"

        det = etree.SubElement(inf, "detEvento", versao="1.00")
        etree.SubElement(det, "descEvento").text = self._descricao_manifestacao(tipo_manifestacao)

        if tipo_manifestacao == self.TP_EVENTO_NAO_REALIZADA:
            etree.SubElement(det, "xJust").text = (justificativa or "").strip()

        con = self._build_comunicacao()
        resposta = con.evento("nfe", evento, id_lote=1)
        xml_text = self._response_to_text(resposta)

        path = self._save_manifestacao_response(
            chave=chave,
            tipo_manifestacao=tipo_manifestacao,
            xml_text=xml_text,
        )

        root = ET.fromstring(xml_text)
        cstat = self._find_text_anywhere(root, "cStat")
        xmotivo = self._find_text_anywhere(root, "xMotivo")
        protocolo = self._find_text_anywhere(root, "nProt")

        return {
            "sucesso": str(cstat) in {"128", "135", "136"},
            "cstat": cstat,
            "xmotivo": xmotivo,
            "protocolo": protocolo,
            "xml_path": str(path),
            "tipo_manifestacao": tipo_manifestacao,
            "chave": chave,
        }

    def _build_comunicacao(self) -> ComunicacaoSefaz:
        homologacao = self._is_homologacao(self.ambiente)

        return ComunicacaoSefaz(
            self.uf_autor.lower(),
            self.certificado_path,
            self.certificado_password,
            homologacao,
        )

    def _extract_ret_dist(self, xml_text: str) -> ET.Element:
        root = ET.fromstring(xml_text)
        ret = self._find_first_anywhere(root, "retDistDFeInt")
        if ret is None:
            raise ValueError("retDistDFeInt não encontrado na resposta da distribuição.")
        return ret

    def _response_to_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        if isinstance(response, bytes):
            return response.decode("utf-8")
        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text
        raise ValueError("Resposta inesperada retornada pela PyNFe.")

    def _decode_doczip(self, text: str) -> str:
        raw = base64.b64decode(text.encode("utf-8"))
        try:
            return gzip.decompress(raw).decode("utf-8")
        except OSError:
            return raw.decode("utf-8", errors="ignore")

    def _save_document_xml(self, *, xml_content: str, nsu: str, schema: str) -> Path:
        schema_slug = (
            (schema or "sem_schema")
            .replace(".xsd", "")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )
        nsu_slug = nsu or "sem_nsu"
        digest = hashlib.sha1(xml_content.encode("utf-8")).hexdigest()[:12]
        path = self.storage_dir / f"{nsu_slug}_{schema_slug}_{digest}.xml"
        path.write_text(xml_content, encoding="utf-8")
        return path

    def _save_raw_response(self, xml_text: str) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.storage_dir / f"distribuicao_raw_{ts}.xml"
        path.write_text(xml_text, encoding="utf-8")
        return path

    def _infer_tipo_documento(self, *, schema: str, xml_content: str) -> str:
        schema_lower = (schema or "").lower()

        if "procnfe" in schema_lower:
            return "nfe_proc"

        if "resnfe" in schema_lower:
            return "resumo_nfe"

        if "proceventonfe" in schema_lower or "resevento" in schema_lower:
            return "evento"

        try:
            root = ET.fromstring(xml_content)
            local = self._local_name(root.tag).lower()

            if local in {"nfeproc", "procnfe"}:
                return "nfe_proc"

            if local == "resnfe":
                return "resumo_nfe"

            if "evento" in local:
                return "evento"
        except Exception:
            pass

        return "outro"

    def _find_text(self, parent: ET.Element, local_name: str) -> Optional[str]:
        for child in list(parent):
            if self._local_name(child.tag) == local_name:
                text = (child.text or "").strip()
                return text or None
        return None

    def _find_first_anywhere(self, root: ET.Element, local_name: str) -> Optional[ET.Element]:
        for elem in root.iter():
            if self._local_name(elem.tag) == local_name:
                return elem
        return None

    def _findall_local(self, root: ET.Element, local_name: str) -> list[ET.Element]:
        return [elem for elem in root.iter() if self._local_name(elem.tag) == local_name]

    def _local_name(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def _normalize_nsu(self, value: str | None) -> str:
        digits = self._only_digits(value or "")
        if not digits:
            return "000000000000000"
        return digits.zfill(15)

    def _normalize_uf(self, value: str) -> str:
        uf = (value or "").strip().upper()
        if uf not in self.UFS_VALIDAS:
            raise ValueError(
                "UF inválida para comunicação com a SEFAZ. "
                "Informe a UF real da empresa, por exemplo: MA, SP, GO."
            )
        return uf

    def _is_homologacao(self, ambiente: str) -> bool:
        return (ambiente or "").strip().lower() in {
            "homologacao",
            "homologação",
            "homolog",
            "2",
        }

    def _only_digits(self, value: str) -> str:
        return "".join(ch for ch in str(value) if ch.isdigit())

    def _save_manifestacao_response(self, *, chave: str, tipo_manifestacao: str, xml_text: str) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.storage_dir / f"manifestacao_{tipo_manifestacao}_{chave}_{ts}.xml"
        path.write_text(xml_text, encoding="utf-8")
        return path

    def _find_text_anywhere(self, root: ET.Element, local_name: str) -> Optional[str]:
        elem = self._find_first_anywhere(root, local_name)
        if elem is None:
            return None
        text = (elem.text or "").strip()
        return text or None

    def _descricao_manifestacao(self, tipo_manifestacao: str) -> str:
        mapa = {
            self.TP_EVENTO_CIENCIA: "Ciencia da Operacao",
            self.TP_EVENTO_CONFIRMACAO: "Confirmacao da Operacao",
            self.TP_EVENTO_DESCONHECIMENTO: "Desconhecimento da Operacao",
            self.TP_EVENTO_NAO_REALIZADA: "Operacao nao Realizada",
        }
        return mapa[tipo_manifestacao]