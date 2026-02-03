from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MovimentacaoListItem(BaseModel):
    id: int
    produto_id: int
    evento_id: Optional[int] = None
    aluguel_id: Optional[int] = None
    usuario_id: int

    tipo: str
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
    origem: str

    created_at: datetime

    class Config:
        from_attributes = True
