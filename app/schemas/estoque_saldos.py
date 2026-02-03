from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EstoqueSaldoRead(BaseModel):
    id: int
    produto_id: int
    local_id: int
    quantidade_base: float
    updated_at: datetime

    class Config:
        from_attributes = True


class EstoqueSaldoConsolidadoRead(BaseModel):
    produto_base_id: int
    total_quantidade_base: float
    local_id: Optional[int] = None
