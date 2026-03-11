from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ManifestacaoDestinatarioPayload(BaseModel):
    certificado_fiscal_id: int = Field(gt=0)
    uf_autor: str = Field(min_length=2, max_length=2)
    tipo_manifestacao: str = Field(default="210210", min_length=6, max_length=6)
    justificativa: Optional[str] = None


class ManifestacaoDestinatarioResponse(BaseModel):
    sucesso: bool
    chave: str
    tipo_manifestacao: str
    cstat: Optional[str] = None
    xmotivo: Optional[str] = None
    protocolo: Optional[str] = None
    xml_path: Optional[str] = None
    mensagem: Optional[str] = None


class ManifestacaoComDownloadResponse(BaseModel):
    manifestacao: ManifestacaoDestinatarioResponse
    download_xml: Optional[dict] = None
    mensagem: str