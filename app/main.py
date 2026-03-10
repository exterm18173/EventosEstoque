from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers.unidades_router import router as unidades_router
from app.routers.categorias_produto_router import router as categorias_produto_router
from app.routers.marcas_router import router as marcas_router
from app.routers.produtos_base_router import router as produtos_base_router
from app.routers.produtos_router import router as produtos_router
from app.routers.produto_embalagens_router import router as produto_embalagens_router
from app.routers.codigos_barras_router import router as codigos_barras_router
from app.routers.produtos_categorias_router import router as produtos_categorias_router
from app.routers.locais_router import router as locais_router
from app.routers.estoque_saldos_router import router as estoque_saldos_router
from app.routers.lotes_router import router as lotes_router
from app.routers.movimentacoes_router import router as movimentacoes_router
from app.routers.clientes_router import router as clientes_router
from app.routers.eventos_router import router as eventos_router
from app.routers.fornecedores_router import router as fornecedores_router
from app.routers.nfe_router import router as nfe_router
from app.routers.compras_router import router as compras_router
from app.routers.alugueis_router import router as alugueis_router
from app.routers.despesas_router import router as despesas_router
from app.routers.relatorios_router import router as relatorios_router
from app.routers.barcode_router import router as barcode_router
from app.routers.usuarios import router as usuarios
from app.routers.orcamentos import router as orcamentos
from app.routers.dashboard_eventos import router as dashboard_eventos
from app.routers.mao_de_obra import router as mao_de_obra
from app.routers.mao_de_obra_modelos import router as mao_de_obra_modelos
from app.routers.dashboard_evento_router import router as dashboard_evento_router
from app.routers.setores_consumo import router as setores_consumo

from app.routers.certificados_fiscais_router import router as certificados_fiscais_router
from app.routers.notas_recebidas_router import router as notas_recebidas_router
from app.routers.notas_conciliacao_router import router as notas_conciliacao_router
from app.routers.notas_importacao_router import router as notas_importacao_router
from app.routers.fornecedor_produto_vinculo_router import router as fornecedor_produto_vinculo_router

app = FastAPI(title="Estoque Casa de Eventos", version="0.1.0")

app.include_router(unidades_router, prefix="/api/v1")
app.include_router(categorias_produto_router, prefix="/api/v1")
app.include_router(marcas_router, prefix="/api/v1")
app.include_router(produtos_base_router, prefix="/api/v1")
app.include_router(produtos_router, prefix="/api/v1")
app.include_router(produto_embalagens_router, prefix="/api/v1")
app.include_router(codigos_barras_router, prefix="/api/v1")
app.include_router(barcode_router, prefix="/api/v1")
app.include_router(produtos_categorias_router, prefix="/api/v1")
app.include_router(locais_router, prefix="/api/v1")
app.include_router(estoque_saldos_router, prefix="/api/v1")
app.include_router(lotes_router, prefix="/api/v1")
app.include_router(movimentacoes_router, prefix="/api/v1")
app.include_router(clientes_router, prefix="/api/v1")
app.include_router(eventos_router, prefix="/api/v1")
app.include_router(fornecedores_router, prefix="/api/v1")
app.include_router(nfe_router, prefix="/api/v1")
app.include_router(compras_router, prefix="/api/v1")
app.include_router(alugueis_router, prefix="/api/v1")
app.include_router(despesas_router, prefix="/api/v1")
app.include_router(relatorios_router, prefix="/api/v1")
app.include_router(usuarios, prefix="/api/v1")
app.include_router(orcamentos, prefix="/api/v1")
app.include_router(dashboard_eventos, prefix="/api/v1")
app.include_router(dashboard_evento_router, prefix="/api/v1")
app.include_router(setores_consumo, prefix="/api/v1")

app.include_router(certificados_fiscais_router, prefix="/api/v1")
app.include_router(notas_recebidas_router, prefix="/api/v1")
app.include_router(notas_conciliacao_router, prefix="/api/v1")
app.include_router(notas_importacao_router, prefix="/api/v1")
app.include_router(fornecedor_produto_vinculo_router, prefix="/api/v1")



app.include_router(mao_de_obra, prefix="/api/v1")
app.include_router(mao_de_obra_modelos, prefix="/api/v1")
app.mount("/media", StaticFiles(directory="storage"), name="media")

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
