from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MovimentacaoCreate(BaseModel):
    produto_id: int
    usuario_id: int

    # contexto (opcional)
    evento_id: Optional[int] = None
    aluguel_id: Optional[int] = None

    # tipo e origem
    tipo: str = Field(min_length=1, max_length=30)   # entrada|saida|transferencia|ajuste
    origem: str = Field(min_length=1, max_length=30) # compra|uso_evento|aluguel|inventario|xml|manual

    # quantidade
    quantidade_informada: float = Field(gt=0)
    unidade_informada_id: int
    fator_para_base: float = Field(gt=0)

    # custo opcional (entrada e ajuste geralmente usam)
    custo_unitario: Optional[float] = None

    # locais
    local_origem_id: Optional[int] = None
    local_destino_id: Optional[int] = None

    # lote / embalagem / barcode
    lote_id: Optional[int] = None
    embalagem_id: Optional[int] = None
    barcode_lido: Optional[str] = None

    observacao: Optional[str] = None


class MovimentacaoRead(BaseModel):
    id: int
    produto_id: int
    usuario_id: int

    evento_id: Optional[int] = None
    aluguel_id: Optional[int] = None

    tipo: str
    origem: str

    quantidade_informada: float
    unidade_informada_id: int
    fator_para_base: float
    quantidade_base: float

    custo_unitario: Optional[float] = None

    local_origem_id: Optional[int] = None
    local_destino_id: Optional[int] = None

    lote_id: Optional[int] = None
    embalagem_id: Optional[int] = None
    barcode_lido: Optional[str] = None

    observacao: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MovimentacaoEstornoResponse(BaseModel):
    movimentacao_original_id: int
    movimentacao_estorno_id: int
