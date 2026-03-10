from pydantic import BaseModel, Field


class OrcamentoItemBase(BaseModel):
    produto_id: int | None = None
    quantidade_base: float | None = None
    valor_unitario: float | None = None
    observacao: str | None = None


class OrcamentoItemCreate(OrcamentoItemBase):
    produto_id: int = Field(..., gt=0)
    quantidade_base: float = Field(..., gt=0)
    valor_unitario: float = Field(..., ge=0)


class OrcamentoItemUpdate(OrcamentoItemBase):
    pass


class OrcamentoItemRead(BaseModel):
    id: int
    orcamento_id: int
    produto_id: int
    quantidade_base: float
    valor_unitario: float
    observacao: str | None = None

    class Config:
        from_attributes = True
