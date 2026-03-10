from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.nota_recebida_item import NotaRecebidaItemResumo


class NotaImportacaoPreviewItem(BaseModel):
    item_id: int
    numero_item: int
    descricao: str
    codigo_barras: Optional[str] = None
    quantidade: float
    valor_unitario: Optional[float] = None
    valor_total: Optional[float] = None

    produto_id: Optional[int] = None
    embalagem_id: Optional[int] = None
    unidade_informada_id: Optional[int] = None
    lote_id: Optional[int] = None
    fator_para_base: Optional[float] = None

    acao: Optional[str] = None
    validado: bool = False
    pronto_para_importar: bool = False
    observacao: Optional[str] = None


class NotaImportacaoPreviewResponse(BaseModel):
    nota_recebida_id: int
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    fornecedor_cnpj: Optional[str] = None

    numero: Optional[str] = None
    serie: Optional[str] = None
    chave_acesso: str

    total_itens: int
    itens_prontos: int
    itens_pendentes: int
    itens_ignorados: int

    valor_total_nota: Optional[float] = None

    itens: List[NotaImportacaoPreviewItem]


class NotaImportacaoGerarCompraRequest(BaseModel):
    usuario_id: int = Field(gt=0)
    fornecedor_id: Optional[int] = Field(default=None, gt=0)
    observacao: Optional[str] = None


class NotaImportacaoGerarCompraResponse(BaseModel):
    nota_recebida_id: int
    compra_id: int
    status_nota: str
    status_compra: str
    itens_criados: int
    mensagem: str


class NotaImportacaoConfirmarCompraRequest(BaseModel):
    usuario_id: int = Field(gt=0)
    local_destino_id: int = Field(gt=0)
    origem: str = Field(default="nota_fiscal", max_length=30)
    observacao: Optional[str] = None


class NotaImportacaoConfirmarCompraResponse(BaseModel):
    nota_recebida_id: int
    compra_id: int
    status_nota: str
    status_compra: str
    movimentacoes_criadas: int
    mensagem: str


class NotaImportacaoResumoResponse(BaseModel):
    nota_recebida_id: int
    compra_id: Optional[int] = None

    total_itens: int
    pendentes: int
    vinculados: int
    novos_produtos: int
    ignorados: int
    conflitos: int

    pronta_para_gerar_compra: bool
    pronta_para_confirmar: bool