from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import date

import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from sqlalchemy import select

from fastapi import UploadFile

from app.models.nfe_documentos import NfeDocumento
from app.models.nfe_itens import NfeItem
from app.models.fornecedores import Fornecedor
from app.models.unidades import Unidade


def _storage_dir() -> Path:
    # salva em: <projeto>/storage/nfe
    base = Path(__file__).resolve().parents[2]
    d = base / "storage" / "nfe"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _as_float(txt: str | None) -> float | None:
    if txt is None:
        return None
    t = txt.strip().replace(",", ".")
    try:
        return float(t)
    except Exception:
        return None


def _as_date(txt: str | None) -> date | None:
    if not txt:
        return None
    t = txt.strip()
    # dhEmi pode vir "2026-01-10T10:00:00-03:00"
    try:
        return date.fromisoformat(t[:10])
    except Exception:
        return None


def _find_text(root: ET.Element, path: str) -> str | None:
    # usa namespace wildcard: { * }
    el = root.find(path)
    return el.text.strip() if (el is not None and el.text) else None


def _extract_chave_acesso(root: ET.Element) -> str | None:
    # infNFe Id="NFe351...."
    inf = root.find(".//{*}infNFe")
    if inf is None:
        return None
    _id = inf.attrib.get("Id") or inf.attrib.get("id")
    if not _id:
        return None
    return _id.replace("NFe", "").strip()


class NfeService:
    def list_documentos(self, db: Session) -> list[NfeDocumento]:
        stmt = select(NfeDocumento).order_by(NfeDocumento.recebida_em.desc())
        return list(db.execute(stmt).scalars().all())

    def get_documento(self, db: Session, doc_id: int) -> NfeDocumento:
        doc = db.get(NfeDocumento, doc_id)
        if not doc:
            raise ValueError("Documento NF-e não encontrado.")
        return doc

    def list_itens(self, db: Session, doc_id: int) -> list[NfeItem]:
        self.get_documento(db, doc_id)
        stmt = select(NfeItem).where(NfeItem.nfe_documento_id == doc_id).order_by(NfeItem.id.asc())
        return list(db.execute(stmt).scalars().all())

    def update_item(self, db: Session, item_id: int, *, produto_id_sugerido, embalagem_id_sugerida, fator_sugerido, status) -> NfeItem:
        item = db.get(NfeItem, item_id)
        if not item:
            raise ValueError("Item NF-e não encontrado.")

        if produto_id_sugerido is not None:
            item.produto_id_sugerido = produto_id_sugerido
        if embalagem_id_sugerida is not None:
            item.embalagem_id_sugerida = embalagem_id_sugerida
        if fator_sugerido is not None:
            item.fator_sugerido = float(fator_sugerido)
        if status is not None:
            item.status = status.strip()

        db.commit()
        db.refresh(item)
        return item

    def upload_xml(self, db: Session, *, usuario_id: int | None, file: UploadFile) -> NfeDocumento:
        xml_bytes = file.file.read()
        if not xml_bytes:
            raise ValueError("Arquivo XML vazio.")

        xml_hash = _sha256_bytes(xml_bytes)

        # tenta parsear
        try:
            root = ET.fromstring(xml_bytes)
        except Exception:
            raise ValueError("XML inválido ou malformado.")

        chave = _extract_chave_acesso(root)
        if not chave:
            raise ValueError("Não foi possível extrair a chave de acesso do XML.")

        # duplicidade por chave
        exists = db.execute(select(NfeDocumento).where(NfeDocumento.chave_acesso == chave)).scalar_one_or_none()
        if exists:
            # marca como duplicada (sem sobrescrever arquivo)
            exists.status_importacao = "duplicada"
            db.commit()
            return exists

        numero = _find_text(root, ".//{*}ide/{*}nNF")
        serie = _find_text(root, ".//{*}ide/{*}serie")
        dh_emi = _find_text(root, ".//{*}ide/{*}dhEmi") or _find_text(root, ".//{*}ide/{*}dEmi")
        data_emissao = _as_date(dh_emi)
        valor_total = _as_float(_find_text(root, ".//{*}ICMSTot/{*}vNF"))

        # emitente (fornecedor)
        emit_doc = _find_text(root, ".//{*}emit/{*}CNPJ") or _find_text(root, ".//{*}emit/{*}CPF")
        emit_nome = _find_text(root, ".//{*}emit/{*}xNome")

        fornecedor_id = None
        if emit_doc:
            emit_doc = emit_doc.strip()
            fornecedor = db.execute(select(Fornecedor).where(Fornecedor.documento == emit_doc)).scalar_one_or_none()
            if not fornecedor:
                fornecedor = Fornecedor(nome=(emit_nome or "Fornecedor").strip(), documento=emit_doc)
                db.add(fornecedor)
                db.flush()
            fornecedor_id = fornecedor.id

        # salva arquivo em disco
        out_dir = _storage_dir()
        out_path = out_dir / f"{chave}.xml"
        out_path.write_bytes(xml_bytes)

        doc = NfeDocumento(
            fornecedor_id=fornecedor_id,
            usuario_id=usuario_id,
            chave_acesso=chave,
            numero=numero,
            serie=serie,
            data_emissao=data_emissao,
            valor_total=valor_total,
            status_importacao="recebida",
            xml_path=str(out_path),
            xml_hash=xml_hash,
        )
        db.add(doc)
        db.flush()

        # cria itens
        dets = root.findall(".//{*}det")
        for det in dets:
            xprod = _find_text(det, ".//{*}prod/{*}xProd")
            ean = _find_text(det, ".//{*}prod/{*}cEAN")
            ncm = _find_text(det, ".//{*}prod/{*}NCM")
            ucom = _find_text(det, ".//{*}prod/{*}uCom")
            qcom = _as_float(_find_text(det, ".//{*}prod/{*}qCom"))
            vun = _as_float(_find_text(det, ".//{*}prod/{*}vUnCom"))
            vprod = _as_float(_find_text(det, ".//{*}prod/{*}vProd"))

            unidade_xml_id = None
            if ucom:
                # tenta mapear unidade pela sigla
                uni = db.execute(select(Unidade).where(Unidade.sigla == ucom.strip())).scalar_one_or_none()
                if uni:
                    unidade_xml_id = uni.id

            item = NfeItem(
                nfe_documento_id=doc.id,
                descricao_xml=xprod,
                ean_xml=(ean if ean and ean != "SEM GTIN" else None),
                ncm=ncm,
                unidade_xml_id=unidade_xml_id,
                quantidade_xml=qcom,
                valor_unitario_xml=vun,
                valor_total_xml=vprod,
                status="pendente",
            )
            db.add(item)

        doc.status_importacao = "processada"
        db.commit()
        db.refresh(doc)
        return doc
