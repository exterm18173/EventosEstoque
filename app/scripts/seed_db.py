# app/scripts/seed_db.py
from __future__ import annotations

import argparse
import random
import string
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.clientes import Cliente
from app.models.eventos import Evento
from app.models.despesas import Despesa
from app.models.usuarios import Usuario
from app.models.locais import Local
from app.models.unidades import Unidade
from app.models.marcas import Marca
from app.models.categorias_produto import CategoriaProduto
from app.models.produtos_base import ProdutoBase
from app.models.produtos import Produto
from app.models.estoque_saldos import EstoqueSaldo
from app.models.movimentacoes import Movimentacao
from app.models.orcamento import Orcamento, OrcamentoItem
from app.models.alugueis import Aluguel
from app.models.aluguel_itens import AluguelItem


# ----------------------------
# Helpers
# ----------------------------
def rstr(n: int) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

def pick(seq):
    return seq[random.randrange(0, len(seq))]

def chunked(lst, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]

def rand_phone() -> str:
    # formato simples BR
    return f"({random.randint(11, 99)}) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

def rand_doc() -> str:
    # documento fake
    return f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"

def rand_date_between(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))

def money(min_v=10, max_v=2000) -> float:
    return float(Decimal(str(random.uniform(min_v, max_v))).quantize(Decimal("0.01")))


# ----------------------------
# Seed steps
# ----------------------------
def ensure_base_data(db: Session, *, usuarios: int, locais: int):
    # Usuario
    if db.query(Usuario).count() == 0:
        objs = [
            Usuario(
                nome=f"Usuario {i+1}",
                email=f"user{i+1}@seed.local",
                perfil="admin",
                ativo=True,
            )
            for i in range(usuarios)
        ]
        db.bulk_save_objects(objs)
        db.commit()

    # Unidade
    if db.query(Unidade).count() == 0:
        units = [
            Unidade(sigla="UN", descricao="Unidade"),
            Unidade(sigla="CX", descricao="Caixa"),
            Unidade(sigla="KG", descricao="Quilo"),
        ]
        db.bulk_save_objects(units)
        db.commit()

    # Marca
    if db.query(Marca).count() == 0:
        marcas = [Marca(nome=f"Marca {i+1}") for i in range(50)]
        db.bulk_save_objects(marcas)
        db.commit()

    # CategoriaProduto (bem simples)
    if db.query(CategoriaProduto).count() == 0:
        raiz = CategoriaProduto(nome="Geral", tipo="raiz", parent_id=None)
        db.add(raiz)
        db.commit()
        childs = [
            CategoriaProduto(nome="Louças", tipo="tag", parent_id=raiz.id),
            CategoriaProduto(nome="Mesas", tipo="tag", parent_id=raiz.id),
            CategoriaProduto(nome="Cadeiras", tipo="tag", parent_id=raiz.id),
            CategoriaProduto(nome="Decoração", tipo="tag", parent_id=raiz.id),
            CategoriaProduto(nome="Cozinha", tipo="tag", parent_id=raiz.id),
        ]
        db.bulk_save_objects(childs)
        db.commit()

    # Locais
    if db.query(Local).count() == 0:
        tipos = ["deposito", "caminhao", "salao"]
        objs = [
            Local(nome=f"Local {i+1}", tipo=pick(tipos), descricao=None)
            for i in range(locais)
        ]
        db.bulk_save_objects(objs)
        db.commit()


def seed_produtos(db: Session, *, produtos: int):
    # se já tiver produtos, não duplica
    if db.query(Produto).count() > 0:
        return

    unidades = db.query(Unidade).all()
    marcas = db.query(Marca).all()
    categorias = db.query(CategoriaProduto).all()
    cat_principal = categorias[0] if categorias else None

    # ProdutoBase
    bases = [
        ProdutoBase(
            nome_base=f"Produto Base {i+1}",
            categoria_principal_id=(cat_principal.id if cat_principal else None),
            descricao=None,
            ativo=True,
        )
        for i in range(max(1, produtos // 2))
    ]
    db.bulk_save_objects(bases)
    db.commit()

    # Recarrega ids
    bases_ids = [x[0] for x in db.query(ProdutoBase.id).all()]
    marcas_ids = [x[0] for x in db.query(Marca.id).all()]
    unidade_ids = [x[0] for x in db.query(Unidade.id).all()]

    objs = []
    for i in range(produtos):
        objs.append(
            Produto(
                produto_base_id=pick(bases_ids),
                marca_id=pick(marcas_ids) if marcas_ids else None,
                nome_comercial=f"Produto {i+1} {rstr(4)}",
                unidade_base_id=pick(unidade_ids),
                sku=f"SKU-{rstr(10)}",
                ativo=True,
                eh_alugavel=(random.random() < 0.4),
                controla_lote=False,
                controla_validade=False,
                estoque_minimo=None,
                custo_medio=money(5, 200),
                preco_reposicao=money(10, 400),
                foto_path=None,
                foto_mime=None,
                foto_nome_original=None,
            )
        )

    db.bulk_save_objects(objs)
    db.commit()


def seed_saldos(db: Session):
    # cria saldos produto x local (uma linha por par)
    if db.query(EstoqueSaldo).count() > 0:
        return

    produto_ids = [x[0] for x in db.query(Produto.id).all()]
    locais_ids = [x[0] for x in db.query(Local.id).all()]

    objs = []
    for pid in produto_ids:
        # cada produto em 2-3 locais (evita explosão)
        for lid in random.sample(locais_ids, k=min(len(locais_ids), random.randint(2, 3))):
            objs.append(
                EstoqueSaldo(
                    produto_id=pid,
                    local_id=lid,
                    quantidade_base=float(Decimal(str(random.uniform(0, 300))).quantize(Decimal("0.01"))),
                    updated_at=datetime.utcnow(),
                )
            )

    for part in chunked(objs, 5000):
        db.bulk_save_objects(part)
        db.commit()


def seed_clientes_eventos(db: Session, *, clientes: int, eventos: int):
    if db.query(Cliente).count() == 0:
        objs = [
            Cliente(
                nome=f"Cliente {i+1} {rstr(3)}",
                documento=rand_doc(),
                telefone=rand_phone(),
                email=f"cliente{i+1}@seed.local",
            )
            for i in range(clientes)
        ]
        for part in chunked(objs, 5000):
            db.bulk_save_objects(part)
            db.commit()

    cliente_ids = [x[0] for x in db.query(Cliente.id).all()]
    if db.query(Evento).count() == 0:
        hoje = date.today()
        start = hoje - timedelta(days=365)
        end = hoje + timedelta(days=365)

        objs = []
        for i in range(eventos):
            di = rand_date_between(start, end)
            df = di + timedelta(days=random.randint(0, 2))
            status = "ativo"
            # marca alguns como encerrados/cancelados
            r = random.random()
            if df < hoje and r < 0.75:
                status = "encerrado"
            elif r > 0.97:
                status = "cancelado"

            objs.append(
                Evento(
                    cliente_id=pick(cliente_ids),
                    nome=f"Evento {i+1} {rstr(5)}",
                    data_inicio=di,
                    data_fim=df,
                    status=status,
                    local_evento=f"Local {random.randint(1,50)}",
                    observacao=None,
                )
            )

        for part in chunked(objs, 5000):
            db.bulk_save_objects(part)
            db.commit()


def seed_despesas(db: Session, *, despesas: int):
    if db.query(Despesa).count() > 0:
        return

    evento_ids = [x[0] for x in db.query(Evento.id).all()]
    categorias = ["Buffet", "Transporte", "Decoração", "Manutenção", "Equipe", "Outros"]
    formas = ["pix", "dinheiro", "cartao", "boleto", None]

    objs = []
    for _ in range(despesas):
        eid = pick(evento_ids) if random.random() < 0.85 else None  # algumas sem evento
        dt = date.today() - timedelta(days=random.randint(0, 400))
        objs.append(
            Despesa(
                data=dt,
                descricao=f"Despesa {rstr(6)}",
                valor=money(20, 2500),
                categoria=pick(categorias),
                forma_pagamento=pick(formas),
                fornecedor_nome=None,
                documento_ref=None,
                evento_id=eid,
                observacao=None,
            )
        )

    for part in chunked(objs, 5000):
        db.bulk_save_objects(part)
        db.commit()


def seed_movimentacoes(db: Session, *, movs: int):
    if db.query(Movimentacao).count() > 0:
        return

    produto_ids = [x[0] for x in db.query(Produto.id).all()]
    evento_ids = [x[0] for x in db.query(Evento.id).all()]
    usuario_ids = [x[0] for x in db.query(Usuario.id).all()]
    unidade_ids = [x[0] for x in db.query(Unidade.id).all()]
    locais_ids = [x[0] for x in db.query(Local.id).all()]

    tipos = ["saida", "devolucao", "ajuste", "perda", "transferencia"]
    origens = ["uso_evento", "inventario", "xml", "compra"]

    objs = []
    for _ in range(movs):
        eid = pick(evento_ids) if random.random() < 0.7 else None
        tipo = pick(tipos)
        # normalmente dashboard de evento liga muito em saida/devolucao
        if eid is not None:
            tipo = "saida" if random.random() < 0.75 else "devolucao"

        q_inf = float(Decimal(str(random.uniform(1, 50))).quantize(Decimal("0.01")))
        fator = 1.0
        q_base = q_inf * fator

        loc_or = pick(locais_ids) if tipo in ("saida", "transferencia") else None
        loc_de = pick(locais_ids) if tipo in ("devolucao", "transferencia") else None

        objs.append(
            Movimentacao(
                produto_id=pick(produto_ids),
                evento_id=eid,
                aluguel_id=None,
                usuario_id=pick(usuario_ids),
                tipo=tipo,
                quantidade_informada=q_inf,
                unidade_informada_id=pick(unidade_ids),
                fator_para_base=fator,
                quantidade_base=q_base,
                custo_unitario=None,
                local_origem_id=loc_or,
                local_destino_id=loc_de,
                lote_id=None,
                embalagem_id=None,
                barcode_lido=None,
                observacao=None,
                origem=pick(origens),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 400)),
            )
        )

    for part in chunked(objs, 5000):
        db.bulk_save_objects(part)
        db.commit()


def seed_orcamentos(db: Session, *, orcamentos: int, itens_por_orcamento: int):
    if db.query(Orcamento).count() > 0:
        return

    cliente_ids = [x[0] for x in db.query(Cliente.id).all()]
    evento_ids = [x[0] for x in db.query(Evento.id).all()]
    produto_ids = [x[0] for x in db.query(Produto.id).all()]

    statuses = ["rascunho", "enviado", "aprovado", "reprovado", "convertido", "cancelado"]

    orcs = []
    for _ in range(orcamentos):
        eid = pick(evento_ids) if random.random() < 0.75 else None
        orcs.append(
            Orcamento(
                cliente_id=pick(cliente_ids) if random.random() < 0.9 else None,
                evento_id=eid,
                data_saida_prevista=None,
                data_devolucao_prevista=None,
                status=pick(statuses),
                valor_total=None,
                observacao=None,
            )
        )

    for part in chunked(orcs, 2000):
        db.bulk_save_objects(part)
        db.commit()

    # itens
    orc_ids = [x[0] for x in db.query(Orcamento.id).all()]
    itens = []
    for oid in random.sample(orc_ids, k=min(len(orc_ids), orcamentos)):
        for _ in range(itens_por_orcamento):
            q = float(Decimal(str(random.uniform(1, 20))).quantize(Decimal("0.0001")))
            vu = money(5, 200)
            itens.append(
                OrcamentoItem(
                    orcamento_id=oid,
                    produto_id=pick(produto_ids),
                    quantidade_base=q,
                    valor_unitario=vu,
                    observacao=None,
                )
            )

    for part in chunked(itens, 5000):
        db.bulk_save_objects(part)
        db.commit()


def seed_alugueis(db: Session, *, alugueis: int, itens_por_aluguel: int):
    if db.query(Aluguel).count() > 0:
        return

    cliente_ids = [x[0] for x in db.query(Cliente.id).all()]
    evento_ids = [x[0] for x in db.query(Evento.id).all()]
    produto_ids = [x[0] for x in db.query(Produto.id).all()]

    statuses = ["rascunho", "confirmado", "em_andamento", "devolvido", "cancelado"]

    hoje = date.today()
    als = []
    for _ in range(alugueis):
        eid = pick(evento_ids) if random.random() < 0.7 else None
        d_saida = hoje - timedelta(days=random.randint(0, 200))
        d_prev = d_saida + timedelta(days=random.randint(1, 7))
        d_real = d_prev if random.random() < 0.6 else None

        st = pick(statuses)
        if d_real is not None and st not in ("cancelado",):
            st = "devolvido"

        als.append(
            Aluguel(
                cliente_id=pick(cliente_ids),
                evento_id=eid,
                data_saida_prevista=d_saida,
                data_devolucao_prevista=d_prev,
                data_devolucao_real=d_real,
                status=st,
                valor_total=None,
                observacao=None,
            )
        )

    for part in chunked(als, 2000):
        db.bulk_save_objects(part)
        db.commit()

    aluguel_ids = [x[0] for x in db.query(Aluguel.id).all()]
    itens = []
    for aid in random.sample(aluguel_ids, k=min(len(aluguel_ids), alugueis)):
        for _ in range(itens_por_aluguel):
            q = float(Decimal(str(random.uniform(1, 30))).quantize(Decimal("0.01")))
            devolvida = q if random.random() < 0.7 else float(Decimal(str(q * random.uniform(0.0, 0.9))).quantize(Decimal("0.01")))
            status_item = "ok"
            if devolvida < q:
                status_item = pick(["faltando", "danificado", "ok"])
            itens.append(
                AluguelItem(
                    aluguel_id=aid,
                    produto_id=pick(produto_ids),
                    quantidade_base=q,
                    quantidade_devolvida_base=devolvida,
                    valor_unitario=money(5, 150) if random.random() < 0.8 else None,
                    status_item=status_item,
                    observacao=None,
                )
            )

    for part in chunked(itens, 5000):
        db.bulk_save_objects(part)
        db.commit()


def reset_tables(db: Session):
    """
    Limpa tudo (CASCADE) — use com cuidado.
    """
    db.execute(text("TRUNCATE TABLE "
                    "aluguel_devolucao_fotos, aluguel_itens, alugueis, "
                    "orcamento_itens, orcamentos, "
                    "movimentacoes, estoque_saldos, lotes, "
                    "produto_codigos_barras, produto_embalagens, produtos_categorias, "
                    "produtos, produtos_base, categorias_produto, marcas, unidades, "
                    "despesas, compras_itens, compras, nfe_itens, nfe_documentos, "
                    "eventos, clientes, fornecedores, locais, usuarios "
                    "RESTART IDENTITY CASCADE;"))
    db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Limpa tabelas (TRUNCATE CASCADE) antes de inserir")

    parser.add_argument("--usuarios", type=int, default=5)
    parser.add_argument("--locais", type=int, default=10)
    parser.add_argument("--produtos", type=int, default=5000)

    parser.add_argument("--clientes", type=int, default=2000)
    parser.add_argument("--eventos", type=int, default=10000)

    parser.add_argument("--despesas", type=int, default=80000)
    parser.add_argument("--movs", type=int, default=300000)

    parser.add_argument("--orcamentos", type=int, default=6000)
    parser.add_argument("--orc_itens", type=int, default=10)

    parser.add_argument("--alugueis", type=int, default=4000)
    parser.add_argument("--al_itens", type=int, default=10)

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset:
            reset_tables(db)

        ensure_base_data(db, usuarios=args.usuarios, locais=args.locais)
        seed_produtos(db, produtos=args.produtos)
        seed_saldos(db)
        seed_clientes_eventos(db, clientes=args.clientes, eventos=args.eventos)
        seed_despesas(db, despesas=args.despesas)
        seed_movimentacoes(db, movs=args.movs)
        seed_orcamentos(db, orcamentos=args.orcamentos, itens_por_orcamento=args.orc_itens)
        seed_alugueis(db, alugueis=args.alugueis, itens_por_aluguel=args.al_itens)

        print("✅ Seed finalizado com sucesso!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
