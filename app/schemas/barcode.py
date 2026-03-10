from pydantic import BaseModel
from typing import Optional


class BarcodeLookupResponse(BaseModel):
    codigo: Optional[str] = None

    produto_id: int
    produto_nome: str

    embalagem_id: Optional[int] = None
    embalagem_nome: Optional[str] = None

    unidade_informada_id: int
    unidade_sigla: str
    fator_para_base: float

    saldo_local_id: Optional[int] = None
    saldo_base: Optional[float] = None

    # imagem pública para o frontend
    foto_url: Optional[str] = None
    foto_mime: Optional[str] = None
    foto_nome_original: Optional[str] = None

    class Config:
        from_attributes = True