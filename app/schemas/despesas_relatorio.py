from typing import Optional
from pydantic import BaseModel


class DespesaResumoRow(BaseModel):
    chave: str  # ex: "2026-02" ou "combustivel" ou "evento:12"
    total: float


class DespesaResumoResponse(BaseModel):
    agrupamento: str  # periodo|categoria|evento
    inicio: Optional[str] = None
    fim: Optional[str] = None
    rows: list[DespesaResumoRow]
