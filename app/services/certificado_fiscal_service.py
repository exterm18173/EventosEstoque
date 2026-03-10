from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.certificado_fiscal import CertificadoFiscal
from app.schemas.certificado_fiscal import (
    CertificadoFiscalCreate,
    CertificadoFiscalUpdate,
    CertificadoFiscalTesteResponse,
)
from app.integrations.sefaz.certificado_manager import CertificadoManager


class CertificadoFiscalService:
    def list(self, db: Session, *, ativo: Optional[bool] = None) -> list[CertificadoFiscal]:
        stmt = select(CertificadoFiscal)

        if ativo is not None:
            stmt = stmt.where(CertificadoFiscal.ativo == ativo)

        stmt = stmt.order_by(CertificadoFiscal.empresa_nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, certificado_id: int) -> CertificadoFiscal:
        obj = db.get(CertificadoFiscal, certificado_id)
        if not obj:
            raise ValueError("Certificado fiscal não encontrado.")
        return obj

    def create(self, db: Session, data: CertificadoFiscalCreate) -> CertificadoFiscal:
        existente = db.execute(
            select(CertificadoFiscal).where(CertificadoFiscal.cnpj == data.cnpj)
        ).scalar_one_or_none()
        if existente:
            raise ValueError("Já existe um certificado cadastrado para este CNPJ.")

        arquivo_path = self._normalize_file_path(data.arquivo_path)

        obj = CertificadoFiscal(
            empresa_nome=data.empresa_nome.strip(),
            cnpj=self._only_digits(data.cnpj),
            ambiente=data.ambiente.strip(),
            tipo_certificado=data.tipo_certificado.strip(),
            arquivo_path=str(arquivo_path),
            senha_criptografada=self._encode_password(data.senha),
            sincronizacao_automatica=data.sincronizacao_automatica,
            ativo=data.ativo,
            observacao=data.observacao.strip() if data.observacao else None,
        )

        # tenta ler validade já no cadastro
        meta = self._try_read_certificate_metadata(obj.arquivo_path, data.senha)
        if meta:
            obj.data_validade = meta.get("data_validade")

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, certificado_id: int, data: CertificadoFiscalUpdate) -> CertificadoFiscal:
        obj = self.get(db, certificado_id)

        if data.empresa_nome is not None:
            obj.empresa_nome = data.empresa_nome.strip()

        if data.cnpj is not None:
            cnpj = self._only_digits(data.cnpj)
            existente = db.execute(
                select(CertificadoFiscal).where(
                    CertificadoFiscal.cnpj == cnpj,
                    CertificadoFiscal.id != certificado_id,
                )
            ).scalar_one_or_none()
            if existente:
                raise ValueError("Já existe outro certificado cadastrado para este CNPJ.")
            obj.cnpj = cnpj

        if data.ambiente is not None:
            obj.ambiente = data.ambiente.strip()

        if data.tipo_certificado is not None:
            obj.tipo_certificado = data.tipo_certificado.strip()

        if data.arquivo_path is not None:
            obj.arquivo_path = str(self._normalize_file_path(data.arquivo_path))

        if data.senha is not None:
            obj.senha_criptografada = self._encode_password(data.senha)

        if data.sincronizacao_automatica is not None:
            obj.sincronizacao_automatica = data.sincronizacao_automatica

        if data.ativo is not None:
            obj.ativo = data.ativo

        if data.observacao is not None:
            obj.observacao = data.observacao.strip() if data.observacao else None

        # revalida certificado se arquivo ou senha mudarem
        if data.arquivo_path is not None or data.senha is not None:
            senha = data.senha if data.senha is not None else self._decode_password(obj.senha_criptografada)
            meta = self._try_read_certificate_metadata(obj.arquivo_path, senha)
            obj.data_validade = meta.get("data_validade") if meta else None

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, certificado_id: int) -> None:
        obj = self.get(db, certificado_id)
        db.delete(obj)
        db.commit()

    def testar(self, db: Session, certificado_id: int) -> CertificadoFiscalTesteResponse:
        obj = self.get(db, certificado_id)
        senha = self._decode_password(obj.senha_criptografada)

        try:
            meta = CertificadoManager().load_metadata(obj.arquivo_path, senha)
            obj.data_validade = meta.get("data_validade")
            db.commit()

            return CertificadoFiscalTesteResponse(
                sucesso=True,
                mensagem="Certificado validado com sucesso.",
                data_validade=meta.get("data_validade"),
                titular=meta.get("titular"),
                documento_titular=meta.get("documento_titular"),
            )
        except Exception as e:
            return CertificadoFiscalTesteResponse(
                sucesso=False,
                mensagem=f"Falha ao validar certificado: {str(e)}",
            )

    def get_plain_password(self, certificado: CertificadoFiscal) -> str:
        return self._decode_password(certificado.senha_criptografada)

    def atualizar_sincronizacao(
        self,
        db: Session,
        certificado: CertificadoFiscal,
        *,
        ultimo_nsu: Optional[str],
    ) -> None:
        certificado.ultima_sincronizacao = datetime.utcnow()
        if ultimo_nsu is not None:
            certificado.ultimo_nsu = ultimo_nsu
        db.commit()

    def _normalize_file_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if not path.exists():
            raise ValueError("Arquivo do certificado não encontrado.")
        if path.suffix.lower() not in {".pfx", ".p12"}:
            raise ValueError("Certificado inválido. Use arquivo .pfx ou .p12.")
        return path

    def _only_digits(self, value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())

    def _encode_password(self, raw: str) -> str:
        return base64.b64encode(raw.encode("utf-8")).decode("utf-8")

    def _decode_password(self, encoded: str) -> str:
        return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")

    def _try_read_certificate_metadata(self, arquivo_path: str, senha: str) -> Optional[dict]:
        try:
            return CertificadoManager().load_metadata(arquivo_path, senha)
        except Exception:
            return None