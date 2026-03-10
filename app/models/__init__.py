from .base import Base
from .categorias_produto import CategoriaProduto
from .marcas import Marca
from .unidades import Unidade
from .produtos_base import ProdutoBase
from .produtos import Produto
from .produtos_categorias import ProdutoCategoria
from .produto_embalagens import ProdutoEmbalagem
from .produto_codigos_barras import ProdutoCodigoBarras
from .clientes import Cliente
from .eventos import Evento
from .locais import Local
from .usuarios import Usuario
from .estoque_saldos import EstoqueSaldo
from .lotes import Lote
from .movimentacoes import Movimentacao
from .fornecedores import Fornecedor
from .compras import Compra
from .compras_itens import CompraItem
from .nfe_documentos import NfeDocumento
from .nfe_itens import NfeItem
from .alugueis import Aluguel
from .aluguel_itens import AluguelItem
from app.models.despesas import Despesa
from .orcamento import Orcamento, OrcamentoItem
from .aluguel_devolucao_fotos import AluguelDevolucaoFoto
from .mao_de_obra import MaoDeObraGrupo, MaoDeObraItem
from .mao_de_obra_modelo import MaoDeObraModelo, MaoDeObraModeloGrupo, MaoDeObraModeloItem
from .setores_consumo import SetorConsumo

# ===== NOVOS MODELS DO MÓDULO FISCAL =====
from .certificado_fiscal import CertificadoFiscal
from .nota_recebida import NotaRecebida
from .nota_recebida_item import NotaRecebidaItem
from .nota_conciliacao_item import NotaConciliacaoItem
from .fornecedor_produto_vinculo import FornecedorProdutoVinculo
from .nota_importacao_log import NotaImportacaoLog