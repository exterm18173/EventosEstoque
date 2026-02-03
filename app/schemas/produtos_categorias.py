from pydantic import BaseModel


class ProdutoCategoriaRead(BaseModel):
    id: int
    produto_id: int
    categoria_id: int

    class Config:
        from_attributes = True
