from typing import Optional
from pydantic import BaseModel


class BarcodeLookupResponse(BaseModel):
    codigo: str

    produto_id: int
    produto_nome: str

    embalagem_id: Optional[int] = None
    embalagem_nome: Optional[str] = None

    unidade_informada_id: int
    unidade_sigla: str

    fator_para_base: float
