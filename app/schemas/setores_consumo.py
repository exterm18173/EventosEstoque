from pydantic import BaseModel, ConfigDict, Field


class SetorConsumoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=80)
    ativo: bool = True


class SetorConsumoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool