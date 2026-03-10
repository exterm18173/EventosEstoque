from __future__ import annotations

from datetime import datetime


class CertificadoManager:
    def load_metadata(self, arquivo_path: str, senha: str) -> dict:
        # implementar leitura real do .pfx depois
        return {
            "data_validade": None,
            "titular": None,
            "documento_titular": None,
        }