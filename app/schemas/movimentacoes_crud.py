from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MovimentacaoCreate(BaseModel):
    produto_id: int = Field(gt=0)
    usuario_id: int = Field(gt=0)

    # contexto
    evento_id: Optional[int] = Field(default=None, gt=0)
    aluguel_id: Optional[int] = Field(default=None, gt=0)

    # separação por setor de consumo
    setor_consumo_id: Optional[int] = Field(default=None, gt=0)

    # tipo e origem
    tipo: Literal["entrada", "saida", "transferencia", "ajuste", "devolucao"]
    origem: str = Field(min_length=1, max_length=30)

    # quantidade
    quantidade_informada: float = Field(gt=0)
    unidade_informada_id: int = Field(gt=0)
    fator_para_base: float = Field(gt=0)

    # custo
    custo_unitario: Optional[float] = Field(default=None, ge=0)

    # locais
    local_origem_id: Optional[int] = Field(default=None, gt=0)
    local_destino_id: Optional[int] = Field(default=None, gt=0)

    # lote / embalagem / código lido
    lote_id: Optional[int] = Field(default=None, gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    barcode_lido: Optional[str] = Field(default=None, max_length=64)

    observacao: Optional[str] = Field(default=None, max_length=500)


class MovimentacaoRead(BaseModel):
    id: int
    produto_id: int
    usuario_id: int

    # contexto
    evento_id: Optional[int] = None
    aluguel_id: Optional[int] = None

    # separação por setor de consumo
    setor_consumo_id: Optional[int] = None

    # opcional: ajuda muito no frontend e relatórios
    # pode manter mesmo sem preencher agora
    setor_consumo_nome: Optional[str] = None

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