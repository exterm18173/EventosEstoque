from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotaImportacaoLogRead(BaseModel):
    id: int
    nota_recebida_id: int
    usuario_id: Optional[int] = None
    tipo_evento: str
    mensagem: str
    payload_json: Optional[dict] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True