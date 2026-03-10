from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


# -----------------------
# Meta / Header
# -----------------------

class DashMeta(BaseModel):
    moeda: str = "BRL"
    gerado_em: datetime


class EventoHeader(BaseModel):
    evento_id: int
    nome: str
    cliente_id: int
    cliente_nome: str
    data_inicio: date
    data_fim: date
    status: str
    local_evento: Optional[str] = None


# -----------------------
# KPIs
# -----------------------

class EventoKpis(BaseModel):
    receita_total: float = 0
    custo_total: float = 0
    resultado: float = 0
    margem_pct: Optional[float] = None  # 0..1

    despesas_total: float = 0          # pagamentos
    consumo_total: float = 0           # estoque (buffet/open bar/limpeza etc.)
    mao_de_obra_total: float = 0

    # opcionais (se você tiver convidados)
    convidados: Optional[int] = None
    custo_por_pessoa: Optional[float] = None


# -----------------------
# Charts
# -----------------------

class WaterfallPoint(BaseModel):
    label: str
    value: float
    kind: Literal["income", "cost", "result"]


class Slice(BaseModel):
    label: str
    value: float


class SeriesPoint(BaseModel):
    x: str  # ex "2025-01-15"
    y: float


class ChartPack(BaseModel):
    # Receita -> -Despesas -> -Consumo -> -Mão de Obra -> Resultado
    waterfall: List[WaterfallPoint]

    # Distribuição do custo total
    distribuicao_custos: List[Slice]

    # Séries (opcional): custo por dia, etc.
    custo_por_dia: List[SeriesPoint] = Field(default_factory=list)
    consumo_por_dia: List[SeriesPoint] = Field(default_factory=list)
    despesas_por_dia: List[SeriesPoint] = Field(default_factory=list)


# -----------------------
# Expansíveis - Despesas (pagamentos)
# -----------------------

class DespesaItem(BaseModel):
    id: int
    data: date
    descricao: str
    categoria: str
    valor: float

    fornecedor_nome: Optional[str] = None
    documento_ref: Optional[str] = None
    forma_pagamento: Optional[str] = None
    observacao: Optional[str] = None


class GrupoDespesas(BaseModel):
    key: str
    label: str
    total: float
    itens: List[DespesaItem]


# -----------------------
# Expansíveis - Consumo (estoque)
# -----------------------

class ConsumoProdutoItem(BaseModel):
    produto_id: int
    produto_nome: str

    saida_base: float
    devolucao_base: float
    consumo_base: float

    custo_unitario: float
    custo_total: float


class GrupoConsumo(BaseModel):
    key: str
    categoria: str
    total: float
    itens: List[ConsumoProdutoItem]


# -----------------------
# Expansíveis - Mão de obra
# -----------------------

class MaoDeObraItemRead(BaseModel):
    id: int
    categoria: Optional[str] = None
    nome: str
    quantidade: int
    valor_unitario: Optional[float] = None
    valor_total: float
    observacao: Optional[str] = None


class MaoDeObraGrupoRead(BaseModel):
    id: int
    nome_grupo: str
    tipo_evento: Optional[str] = None
    observacao: Optional[str] = None
    total: float
    itens: List[MaoDeObraItemRead]


# -----------------------
# Response principal (tela inteira)
# -----------------------

class DashSections(BaseModel):
    despesas: List[GrupoDespesas]
    consumo: List[GrupoConsumo]
    mao_de_obra: List[MaoDeObraGrupoRead]


class DashboardResumo(BaseModel):
    # cards “top 5”
    top_despesas: List[Slice] = Field(default_factory=list)
    top_consumo: List[Slice] = Field(default_factory=list)
    top_mao_de_obra: List[Slice] = Field(default_factory=list)


class DashboardEventoDashResponse(BaseModel):
    meta: DashMeta
    header: EventoHeader
    kpis: EventoKpis
    charts: ChartPack
    sections: DashSections
    resumo: DashboardResumo