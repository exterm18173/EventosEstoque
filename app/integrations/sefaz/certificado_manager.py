from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12


class CertificadoManager:
    """
    Responsável por carregar e extrair informações de certificados A1 (.pfx/.p12)
    """

    def load_metadata(self, arquivo_path: str, senha: str) -> dict:
        path = Path(arquivo_path)

        if not path.exists():
            raise ValueError("Arquivo de certificado não encontrado.")

        if path.suffix.lower() not in {".pfx", ".p12"}:
            raise ValueError("Certificado inválido. Use arquivo .pfx ou .p12.")

        with open(path, "rb") as f:
            data = f.read()

        try:
            private_key, certificate, additional = pkcs12.load_key_and_certificates(
                data,
                senha.encode() if senha else None,
            )
        except Exception as e:
            raise ValueError(f"Erro ao abrir certificado: {str(e)}")

        if certificate is None:
            raise ValueError("Não foi possível ler o certificado digital.")

        data_validade = certificate.not_valid_after

        titular = self._extract_titular(certificate)
        documento = self._extract_documento(certificate)

        return {
            "data_validade": data_validade,
            "titular": titular,
            "documento_titular": documento,
        }

    def _extract_titular(self, cert: x509.Certificate) -> Optional[str]:
        try:
            subject = cert.subject.rfc4514_string()

            match = re.search(r"CN=([^,]+)", subject)
            if match:
                return match.group(1)

        except Exception:
            pass

        return None

    def _extract_documento(self, cert: x509.Certificate) -> Optional[str]:
        """
        Extrai CPF ou CNPJ do certificado.
        Normalmente aparece no CN ou no campo serialNumber.
        """

        try:
            subject = cert.subject.rfc4514_string()

            # CNPJ
            match_cnpj = re.search(r"\d{14}", subject)
            if match_cnpj:
                return match_cnpj.group(0)

            # CPF
            match_cpf = re.search(r"\d{11}", subject)
            if match_cpf:
                return match_cpf.group(0)

        except Exception:
            pass

        return None