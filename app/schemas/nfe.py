from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class NfeDocumentoListItem(BaseModel):
    id: int
    fornecedor_id: Optional[int] = None
    usuario_id: Optional[int] = None

    chave_acesso: str
    numero: Optional[str] = None
    serie: Optional[str] = None
    data_emissao: Optional[date] = None
    valor_total: Optional[float] = None

    status_importacao: str
    recebida_em: datetime

    class Config:
        from_attributes = True


class NfeDocumentoRead(NfeDocumentoListItem):
    xml_path: Optional[str] = None
    xml_hash: Optional[str] = None


class NfeItemRead(BaseModel):
    id: int
    nfe_documento_id: int

    descricao_xml: Optional[str] = None
    ean_xml: Optional[str] = None
    ncm: Optional[str] = None

    unidade_xml_id: Optional[int] = None
    quantidade_xml: Optional[float] = None
    valor_unitario_xml: Optional[float] = None
    valor_total_xml: Optional[float] = None

    produto_id_sugerido: Optional[int] = None
    embalagem_id_sugerida: Optional[int] = None
    fator_sugerido: Optional[float] = None

    status: str

    class Config:
        from_attributes = True


class NfeItemUpdate(BaseModel):
    produto_id_sugerido: Optional[int] = None
    embalagem_id_sugerida: Optional[int] = None
    fator_sugerido: Optional[float] = Field(default=None, gt=0)

    status: Optional[str] = Field(default=None, max_length=30)  # pendente|vinculado|ignorado
