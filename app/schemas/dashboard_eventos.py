from __future__ import annotations

from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel


class DashboardKpis(BaseModel):
    eventos: int
    receita_total: float
    despesas_total: float
    consumo_total: float
    custo_total: float
    resultado_total: float


class DashboardEventoResumo(BaseModel):
    evento_id: int
    nome: str
    cliente_id: int
    cliente_nome: str
    data_inicio: date
    data_fim: date
    status: str

    receita: float
    despesas_total: float
    consumo_total: float
    custo_total: float
    resultado: float


class DashboardEventosResumoResponse(BaseModel):
    total_items: int                 # ✅ total real do filtro (sem paginação)
    kpis: DashboardKpis              # ✅ KPIs do filtro inteiro (sem paginação)
    eventos: List[DashboardEventoResumo]


# ===================== DETALHE =====================

class DashboardDespesaItem(BaseModel):
    id: int
    data: date
    descricao: str
    categoria: Optional[str] = None
    valor: float
    fornecedor_nome: Optional[str] = None
    documento_ref: Optional[str] = None
    forma_pagamento: Optional[str] = None


class DashboardConsumoItem(BaseModel):
    produto_id: int
    produto_nome: str
    categoria: str

    saida_base: float
    devolucao_base: float
    consumo_base: float

    custo_unitario: float
    custo_total: float


class DashboardCategoriaTotal(BaseModel):
    tipo: Literal["despesa", "consumo"]
    categoria: str
    total: float


class DashboardEventoDetail(BaseModel):
    evento_id: int
    nome: str
    cliente_id: int
    cliente_nome: str
    data_inicio: date
    data_fim: date
    status: str

    receita: float
    despesas_total: float
    consumo_total: float
    custo_total: float
    resultado: float

    por_categoria: List[DashboardCategoriaTotal]
    despesas: List[DashboardDespesaItem]
    consumo_itens: List[DashboardConsumoItem]