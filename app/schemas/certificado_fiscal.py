from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CertificadoFiscalBase(BaseModel):
    empresa_nome: str = Field(min_length=1, max_length=180)
    cnpj: str = Field(min_length=11, max_length=20)

    ambiente: str = Field(default="producao", max_length=20)
    tipo_certificado: str = Field(default="A1", max_length=20)

    sincronizacao_automatica: bool = False
    ativo: bool = True

    observacao: Optional[str] = None


class CertificadoFiscalCreate(CertificadoFiscalBase):
    senha: str = Field(min_length=1, max_length=255)
    arquivo_path: str = Field(min_length=1)


class CertificadoFiscalUpdate(BaseModel):
    empresa_nome: Optional[str] = Field(default=None, min_length=1, max_length=180)
    cnpj: Optional[str] = Field(default=None, min_length=11, max_length=20)

    ambiente: Optional[str] = Field(default=None, max_length=20)
    tipo_certificado: Optional[str] = Field(default=None, max_length=20)

    senha: Optional[str] = Field(default=None, min_length=1, max_length=255)
    arquivo_path: Optional[str] = None

    sincronizacao_automatica: Optional[bool] = None
    ativo: Optional[bool] = None

    observacao: Optional[str] = None


class CertificadoFiscalRead(BaseModel):
    id: int
    empresa_nome: str
    cnpj: str

    ambiente: str
    tipo_certificado: str

    arquivo_path: str
    data_validade: Optional[datetime] = None

    ultimo_nsu: Optional[str] = None
    ultima_sincronizacao: Optional[datetime] = None

    sincronizacao_automatica: bool
    ativo: bool

    observacao: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CertificadoFiscalListItem(BaseModel):
    id: int
    empresa_nome: str
    cnpj: str
    ambiente: str
    tipo_certificado: str
    data_validade: Optional[datetime] = None
    ultima_sincronizacao: Optional[datetime] = None
    sincronizacao_automatica: bool
    ativo: bool

    class Config:
        from_attributes = True


class CertificadoFiscalTesteResponse(BaseModel):
    sucesso: bool
    mensagem: str
    data_validade: Optional[datetime] = None
    titular: Optional[str] = None
    documento_titular: Optional[str] = None


class CertificadoFiscalSincronizacaoResponse(BaseModel):
    certificado_id: int
    notas_novas: int
    notas_atualizadas: int
    ultimo_nsu: Optional[str] = None
    mensagem: str