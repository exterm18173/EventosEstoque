from pydantic import BaseModel, Field


class OrcamentoToAluguelRequest(BaseModel):
    # opcional: você pode permitir override de campos no momento de converter
    status_aluguel: str = Field(default="aberto")
    copiar_datas: bool = True
    copiar_observacao: bool = True
