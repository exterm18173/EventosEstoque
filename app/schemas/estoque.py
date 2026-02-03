from datetime import datetime
from pydantic import BaseModel


class ProdutoSaldoRead(BaseModel):
    produto_id: int
    local_id: int
    quantidade_base: float
    updated_at: datetime

    class Config:
        from_attributes = True
