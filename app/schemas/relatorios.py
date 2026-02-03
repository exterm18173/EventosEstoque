from typing import Optional
from pydantic import BaseModel


class EstoqueSaldoRow(BaseModel):
    produto_id: int
    produto_nome: str
    local_id: int
    local_nome: str
    quantidade_base: float


class EstoqueSaldoResponse(BaseModel):
    rows: list[EstoqueSaldoRow]


class MovimentacaoRow(BaseModel):
    id: int
    created_at: str

    tipo: str
    origem: Optional[str] = None

    produto_id: int
    produto_nome: str

    quantidade_informada: float
    unidade_informada_id: int
    fator_para_base: float
    quantidade_base: float

    custo_unitario: Optional[float] = None

    evento_id: Optional[int] = None
    aluguel_id: Optional[int] = None

    local_origem_id: Optional[int] = None
    local_destino_id: Optional[int] = None


class MovimentacoesResponse(BaseModel):
    rows: list[MovimentacaoRow]


class CustoEventoResponse(BaseModel):
    evento_id: int
    despesas_total: float
    consumo_estoque_total: float
    total: float
