from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class CompraBase(BaseModel):
    fornecedor_id: int
    usuario_id: int
    nfe_documento_id: Optional[int] = None

    numero_documento: Optional[str] = Field(default=None, max_length=60)
    data_compra: Optional[date] = None
    valor_total: Optional[float] = None

    status: str = Field(default="rascunho", max_length=30)  # rascunho|confirmada|cancelada


class CompraCreate(CompraBase):
    pass


class CompraUpdate(BaseModel):
    fornecedor_id: Optional[int] = None
    usuario_id: Optional[int] = None
    nfe_documento_id: Optional[int] = None

    numero_documento: Optional[str] = Field(default=None, max_length=60)
    data_compra: Optional[date] = None
    valor_total: Optional[float] = None
    status: Optional[str] = Field(default=None, max_length=30)


class CompraRead(CompraBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompraConfirmarRequest(BaseModel):
    # onde vai entrar no estoque
    local_destino_id: int

    # origem da movimentação (compra|xml)
    origem: str = Field(default="compra", max_length=30)

    observacao: Optional[str] = None


class CompraConfirmarResponse(BaseModel):
    compra_id: int
    status: str
    movimentacoes_criadas: int
