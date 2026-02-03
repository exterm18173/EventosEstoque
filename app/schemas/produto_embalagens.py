from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmbalagemBase(BaseModel):
    nome: str = Field(min_length=1, max_length=40)  # unidade|caixa|fardo|pacote
    unidade_id: int
    fator_para_base: float = Field(gt=0)
    permite_fracionar: bool = False
    principal: bool = False


class EmbalagemCreate(EmbalagemBase):
    pass


class EmbalagemUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=40)
    unidade_id: Optional[int] = None
    fator_para_base: Optional[float] = Field(default=None, gt=0)
    permite_fracionar: Optional[bool] = None
    principal: Optional[bool] = None


class EmbalagemRead(EmbalagemBase):
    id: int
    produto_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
