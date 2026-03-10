from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.nota_recebida_item import NotaRecebidaItemCreate, NotaRecebidaItemRead


class NotaRecebidaFiltro(BaseModel):
    certificado_fiscal_id: Optional[int] = Field(default=None, gt=0)
    fornecedor_id: Optional[int] = Field(default=None, gt=0)

    fornecedor_nome: Optional[str] = None
    fornecedor_cnpj: Optional[str] = None

    chave_acesso: Optional[str] = None
    numero: Optional[str] = None
    serie: Optional[str] = None
    modelo: Optional[str] = None

    status: Optional[str] = None

    data_emissao_inicio: Optional[datetime] = None
    data_emissao_fim: Optional[datetime] = None

    data_autorizacao_inicio: Optional[datetime] = None
    data_autorizacao_fim: Optional[datetime] = None


class NotaRecebidaBase(BaseModel):
    certificado_fiscal_id: int = Field(gt=0)

    fornecedor_id: Optional[int] = Field(default=None, gt=0)
    compra_id: Optional[int] = Field(default=None, gt=0)

    chave_acesso: str = Field(min_length=44, max_length=44)
    numero: Optional[str] = Field(default=None, max_length=20)
    serie: Optional[str] = Field(default=None, max_length=10)
    modelo: Optional[str] = Field(default=None, max_length=10)

    fornecedor_nome: str = Field(min_length=1, max_length=180)
    fornecedor_cnpj: Optional[str] = Field(default=None, max_length=20)

    natureza_operacao: Optional[str] = Field(default=None, max_length=255)
    cfop_predominante: Optional[str] = Field(default=None, max_length=10)

    data_emissao: Optional[datetime] = None
    data_autorizacao: Optional[datetime] = None

    valor_total: Optional[float] = Field(default=None, ge=0)
    valor_produtos: Optional[float] = Field(default=None, ge=0)
    valor_frete: Optional[float] = Field(default=None, ge=0)
    valor_desconto: Optional[float] = Field(default=None, ge=0)
    valor_outros: Optional[float] = Field(default=None, ge=0)

    protocolo: Optional[str] = Field(default=None, max_length=40)
    nsu: Optional[str] = Field(default=None, max_length=20)

    status: str = Field(default="nova", max_length=30)

    xml_path: Optional[str] = None
    xml_hash: Optional[str] = Field(default=None, max_length=128)

    observacao: Optional[str] = None
    importada_em: Optional[datetime] = None


class NotaRecebidaCreate(NotaRecebidaBase):
    itens: List[NotaRecebidaItemCreate] = []


class NotaRecebidaRead(NotaRecebidaBase):
    id: int

    created_at: datetime
    updated_at: datetime

    itens: List[NotaRecebidaItemRead] = []

    class Config:
        from_attributes = True


class NotaRecebidaListItem(BaseModel):
    id: int
    certificado_fiscal_id: int
    fornecedor_id: Optional[int] = None
    compra_id: Optional[int] = None

    chave_acesso: str
    numero: Optional[str] = None
    serie: Optional[str] = None
    modelo: Optional[str] = None

    fornecedor_nome: str
    fornecedor_cnpj: Optional[str] = None

    data_emissao: Optional[datetime] = None
    data_autorizacao: Optional[datetime] = None

    valor_total: Optional[float] = None
    status: str
    protocolo: Optional[str] = None
    nsu: Optional[str] = None

    class Config:
        from_attributes = True


class NotaRecebidaDetalhe(BaseModel):
    id: int
    certificado_fiscal_id: int
    fornecedor_id: Optional[int] = None
    compra_id: Optional[int] = None

    chave_acesso: str
    numero: Optional[str] = None
    serie: Optional[str] = None
    modelo: Optional[str] = None

    fornecedor_nome: str
    fornecedor_cnpj: Optional[str] = None

    natureza_operacao: Optional[str] = None
    cfop_predominante: Optional[str] = None

    data_emissao: Optional[datetime] = None
    data_autorizacao: Optional[datetime] = None

    valor_total: Optional[float] = None
    valor_produtos: Optional[float] = None
    valor_frete: Optional[float] = None
    valor_desconto: Optional[float] = None
    valor_outros: Optional[float] = None

    protocolo: Optional[str] = None
    nsu: Optional[str] = None

    status: str
    xml_path: Optional[str] = None
    xml_hash: Optional[str] = None

    observacao: Optional[str] = None
    importada_em: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    itens: List[NotaRecebidaItemRead] = []

    class Config:
        from_attributes = True


class NotaRecebidaStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)
    observacao: Optional[str] = None


class NotaRecebidaResumoImportacao(BaseModel):
    nota_recebida_id: int
    compra_id: Optional[int] = None
    total_itens: int
    pendentes: int
    vinculados: int
    novos_produtos: int
    ignorados: int
    conflitos: int
    valor_total: Optional[float] = None
    pronta_para_importar: bool