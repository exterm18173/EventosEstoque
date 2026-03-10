from datetime import date
from pydantic import BaseModel, Field


class OrcamentoBase(BaseModel):
    cliente_id: int | None = None
    evento_id: int | None = None

    data_saida_prevista: date | None = None
    data_devolucao_prevista: date | None = None

    status: str | None = None
    valor_total: float | None = None
    observacao: str | None = None


class OrcamentoCreate(OrcamentoBase):
    cliente_id: int = Field(..., gt=0)
    status: str | None = "rascunho"


class OrcamentoUpdate(OrcamentoBase):
    pass


class OrcamentoRead(OrcamentoBase):
    id: int

    class Config:
        from_attributes = True


class OrcamentoListItem(BaseModel):
    id: int
    cliente_id: int | None = None
    evento_id: int | None = None
    status: str
    data_saida_prevista: date | None = None
    data_devolucao_prevista: date | None = None
    valor_total: float | None = None

    class Config:
        from_attributes = True
