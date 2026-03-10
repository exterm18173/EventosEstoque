from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


class NotaXmlParserService:
    def parse_file(self, xml_path: str) -> dict[str, Any]:
        path = Path(xml_path)
        if not path.exists():
            raise ValueError("XML não encontrado.")

        xml_bytes = path.read_bytes()
        return self.parse_xml_bytes(xml_bytes, xml_path=str(path))

    def parse_xml_bytes(self, xml_bytes: bytes, *, xml_path: str | None = None) -> dict[str, Any]:
        try:
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            raise ValueError(f"Falha ao ler XML: {str(e)}")

        ns = self._detect_ns(root)

        inf_nfe = root.find(f".//{ns}infNFe")
        prot_nfe = root.find(f".//{ns}protNFe")
        ide = root.find(f".//{ns}ide")
        emit = root.find(f".//{ns}emit")
        total = root.find(f".//{ns}ICMSTot")

        if inf_nfe is None:
            raise ValueError("XML não contém infNFe.")

        chave = inf_nfe.attrib.get("Id", "").replace("NFe", "") or None

        itens = []
        cfops = []

        for det in root.findall(f".//{ns}det"):
            prod = det.find(f"{ns}prod")
            if prod is None:
                continue

            cfop = self._text(prod.find(f"{ns}CFOP"))
            if cfop:
                cfops.append(cfop)

            item = {
                "numero_item": self._safe_int(det.attrib.get("nItem")),
                "codigo_fornecedor": self._text(prod.find(f"{ns}cProd")),
                "codigo_barras": self._normalize_barcode(self._text(prod.find(f"{ns}cEAN"))),
                "descricao": self._text(prod.find(f"{ns}xProd")) or "SEM DESCRIÇÃO",
                "ncm": self._text(prod.find(f"{ns}NCM")),
                "cfop": cfop,
                "unidade_comercial": self._text(prod.find(f"{ns}uCom")),
                "quantidade": self._safe_float(self._text(prod.find(f"{ns}qCom")), default=0.0),
                "valor_unitario": self._safe_float(self._text(prod.find(f"{ns}vUnCom"))),
                "valor_total": self._safe_float(self._text(prod.find(f"{ns}vProd"))),
                "status_conciliacao": "nao_analisado",
                "observacao": None,
            }
            itens.append(item)

        data = {
            "chave_acesso": chave,
            "numero": self._text(ide.find(f"{ns}nNF")) if ide is not None else None,
            "serie": self._text(ide.find(f"{ns}serie")) if ide is not None else None,
            "modelo": self._text(ide.find(f"{ns}mod")) if ide is not None else None,
            "fornecedor_nome": self._text(emit.find(f"{ns}xNome")) if emit is not None else "SEM FORNECEDOR",
            "fornecedor_cnpj": self._only_digits(
                self._text(emit.find(f"{ns}CNPJ")) or self._text(emit.find(f"{ns}CPF")) or ""
            ) or None,
            "natureza_operacao": self._text(ide.find(f"{ns}natOp")) if ide is not None else None,
            "cfop_predominante": self._pick_cfop_predominante(cfops),
            "data_emissao": self._parse_datetime(self._text(ide.find(f"{ns}dhEmi")) if ide is not None else None),
            "data_autorizacao": self._parse_datetime(
                self._text(prot_nfe.find(f".//{ns}dhRecbto")) if prot_nfe is not None else None
            ),
            "valor_total": self._safe_float(self._text(total.find(f"{ns}vNF")) if total is not None else None),
            "valor_produtos": self._safe_float(self._text(total.find(f"{ns}vProd")) if total is not None else None),
            "valor_frete": self._safe_float(self._text(total.find(f"{ns}vFrete")) if total is not None else None),
            "valor_desconto": self._safe_float(self._text(total.find(f"{ns}vDesc")) if total is not None else None),
            "valor_outros": self._safe_float(self._text(total.find(f"{ns}vOutro")) if total is not None else None),
            "protocolo": self._text(prot_nfe.find(f".//{ns}nProt")) if prot_nfe is not None else None,
            "xml_path": xml_path,
            "xml_hash": hashlib.sha256(xml_bytes).hexdigest(),
            "itens": itens,
        }

        if not data["chave_acesso"]:
            raise ValueError("Não foi possível identificar a chave de acesso do XML.")

        return data

    def _detect_ns(self, root: ET.Element) -> str:
        if root.tag.startswith("{"):
            return root.tag.split("}")[0] + "}"
        return ""

    def _text(self, node: ET.Element | None) -> str | None:
        if node is None or node.text is None:
            return None
        value = node.text.strip()
        return value or None

    def _safe_float(self, value: str | None, default: float | None = None) -> float | None:
        if value in (None, ""):
            return default
        try:
            return float(value.replace(",", "."))
        except Exception:
            return default

    def _safe_int(self, value: str | None, default: int = 0) -> int:
        if value in (None, ""):
            return default
        try:
            return int(value)
        except Exception:
            return default

    def _parse_datetime(self, raw: str | None):
        if not raw:
            return None
        try:
            return raw.replace("Z", "+00:00")
        except Exception:
            return raw

    def _normalize_barcode(self, code: str | None) -> str | None:
        if not code:
            return None
        code = code.strip()
        if code.upper() in {"SEM GTIN", "SEMGTIN"}:
            return None
        return code

    def _pick_cfop_predominante(self, cfops: list[str]) -> str | None:
        if not cfops:
            return None
        counts: dict[str, int] = {}
        for cfop in cfops:
            counts[cfop] = counts.get(cfop, 0) + 1
        return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]

    def _only_digits(self, value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())