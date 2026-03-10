from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class AluguelBase(BaseModel):
    cliente_id: int
    evento_id: Optional[int] = None

    data_saida_prevista: date
    data_devolucao_prevista: date
    data_devolucao_real: Optional[date] = None

    status: str = Field(default="aberto", max_length=30)  # aberto|em_andamento|devolvido|cancelado
    valor_total: Optional[float] = None
    observacao: Optional[str] = None


class AluguelCreate(AluguelBase):
    pass


class AluguelUpdate(BaseModel):
    cliente_id: Optional[int] = None
    evento_id: Optional[int] = None

    data_saida_prevista: Optional[date] = None
    data_devolucao_prevista: Optional[date] = None
    data_devolucao_real: Optional[date] = None

    status: Optional[str] = Field(default=None, max_length=30)
    valor_total: Optional[float] = None
    observacao: Optional[str] = None


class AluguelRead(AluguelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AluguelSaidaRequest(BaseModel):
    local_origem_id: int
    usuario_id: int
    origem: str = Field(default="aluguel", max_length=30)
    observacao: Optional[str] = None


class AluguelDevolucaoRequest(BaseModel):
    local_destino_id: int
    usuario_id: int
    origem: str = Field(default="aluguel", max_length=30)
    observacao: Optional[str] = None


class AluguelAcaoResponse(BaseModel):
    aluguel_id: int
    status: str
    movimentacoes_criadas: int
class AluguelDevolverItemRequest(BaseModel):
    local_destino_id: int
    usuario_id: int
    quantidade_devolver_base: float = Field(gt=0)
    origem: str = Field(default="aluguel", max_length=30)
    observacao: Optional[str] = None