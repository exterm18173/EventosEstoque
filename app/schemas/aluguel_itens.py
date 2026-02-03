from typing import Optional

from pydantic import BaseModel, Field


class AluguelItemBase(BaseModel):
    produto_id: int
    quantidade_base: float = Field(gt=0)  # aqui já salva em base (unidade padrão do produto)
    valor_unitario: Optional[float] = None
    status_item: str = Field(default="pendente", max_length=30)  # pendente|retirado|parcial|devolvido
    observacao: Optional[str] = None


class AluguelItemCreate(AluguelItemBase):
    pass


class AluguelItemUpdate(BaseModel):
    produto_id: Optional[int] = None
    quantidade_base: Optional[float] = Field(default=None, gt=0)
    quantidade_devolvida_base: Optional[float] = Field(default=None, ge=0)
    valor_unitario: Optional[float] = None
    status_item: Optional[str] = Field(default=None, max_length=30)
    observacao: Optional[str] = None


class AluguelItemRead(AluguelItemBase):
    id: int
    aluguel_id: int
    quantidade_devolvida_base: float

    class Config:
        from_attributes = True
