from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotaConciliacaoItemBase(BaseModel):
    acao: str = Field(default="pendente", max_length=30)
    # pendente | vincular_existente | criar_produto | ignorar | conflito

    produto_id: Optional[int] = Field(default=None, gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: Optional[int] = Field(default=None, gt=0)

    fator_para_base: Optional[float] = Field(default=None, gt=0)
    barcode_final: Optional[str] = Field(default=None, max_length=64)

    lote_id: Optional[int] = Field(default=None, gt=0)

    criar_produto_novo: bool = False
    nome_produto_sugerido: Optional[str] = Field(default=None, max_length=220)

    observacao: Optional[str] = None
    validado: bool = False


class NotaConciliacaoItemCreate(NotaConciliacaoItemBase):
    nota_recebida_item_id: int = Field(gt=0)


class NotaConciliacaoItemUpdate(BaseModel):
    acao: Optional[str] = Field(default=None, max_length=30)

    produto_id: Optional[int] = Field(default=None, gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: Optional[int] = Field(default=None, gt=0)

    fator_para_base: Optional[float] = Field(default=None, gt=0)
    barcode_final: Optional[str] = Field(default=None, max_length=64)

    lote_id: Optional[int] = Field(default=None, gt=0)

    criar_produto_novo: Optional[bool] = None
    nome_produto_sugerido: Optional[str] = Field(default=None, max_length=220)

    observacao: Optional[str] = None
    validado: Optional[bool] = None


class NotaConciliacaoItemRead(NotaConciliacaoItemBase):
    id: int
    nota_recebida_item_id: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotaItemVincularProdutoRequest(BaseModel):
    produto_id: int = Field(gt=0)
    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: int = Field(gt=0)
    fator_para_base: float = Field(gt=0)
    barcode_final: Optional[str] = Field(default=None, max_length=64)
    lote_id: Optional[int] = Field(default=None, gt=0)
    observacao: Optional[str] = None


class NotaItemCriarProdutoRequest(BaseModel):
    produto_base_id: int = Field(gt=0)
    marca_id: Optional[int] = Field(default=None, gt=0)

    nome_comercial: str = Field(min_length=1, max_length=220)
    unidade_base_id: int = Field(gt=0)

    sku: Optional[str] = Field(default=None, max_length=80)
    ativo: bool = True

    eh_alugavel: bool = False
    controla_lote: bool = False
    controla_validade: bool = False

    estoque_minimo: Optional[float] = Field(default=None, ge=0)
    custo_medio: Optional[float] = Field(default=None, ge=0)
    preco_reposicao: Optional[float] = Field(default=None, ge=0)

    embalagem_id: Optional[int] = Field(default=None, gt=0)
    unidade_informada_id: int = Field(gt=0)
    fator_para_base: float = Field(gt=0)

    barcode_final: Optional[str] = Field(default=None, max_length=64)
    lote_id: Optional[int] = Field(default=None, gt=0)

    observacao: Optional[str] = None


class NotaItemIgnorarRequest(BaseModel):
    observacao: Optional[str] = None


class NotaConciliacaoLoteResumo(BaseModel):
    total_itens: int
    pendentes: int
    vinculados: int
    novos_produtos: int
    ignorados: int
    conflitos: int