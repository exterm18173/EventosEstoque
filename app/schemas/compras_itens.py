from typing import Optional
from pydantic import BaseModel, Field


class CompraItemBase(BaseModel):
    produto_id: int
    embalagem_id: Optional[int] = None

    unidade_informada_id: int
    quantidade_informada: float = Field(gt=0)
    fator_para_base: float = Field(gt=0)
    quantidade_base: Optional[float] = None

    valor_unitario_informado: Optional[float] = None
    valor_total: Optional[float] = None

    lote_id: Optional[int] = None
    barcode_lido: Optional[str] = None


class CompraItemCreate(CompraItemBase):
    pass


class CompraItemUpdate(BaseModel):
    produto_id: Optional[int] = None
    embalagem_id: Optional[int] = None
    unidade_informada_id: Optional[int] = None

    quantidade_informada: Optional[float] = Field(default=None, gt=0)
    fator_para_base: Optional[float] = Field(default=None, gt=0)
    quantidade_base: Optional[float] = None

    valor_unitario_informado: Optional[float] = None
    valor_total: Optional[float] = None

    lote_id: Optional[int] = None
    barcode_lido: Optional[str] = None


class CompraItemRead(CompraItemBase):
    id: int
    compra_id: int

    class Config:
        from_attributes = True
