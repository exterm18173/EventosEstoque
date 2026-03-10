from __future__ import annotations


class DistribuicaoDfeClient:
    def __init__(self, *, certificado_path: str, certificado_password: str, ambiente: str, cnpj: str):
        self.certificado_path = certificado_path
        self.certificado_password = certificado_password
        self.ambiente = ambiente
        self.cnpj = cnpj

    def consultar_documentos(self, *, ultimo_nsu: str | None = None) -> dict:
        # implementar integração real depois
        return {
            "ultimo_nsu": ultimo_nsu,
            "documentos": [],
        }