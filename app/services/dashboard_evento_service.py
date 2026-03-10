from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, case, literal

from app.models.eventos import Evento
from app.models.clientes import Cliente
from app.models.despesas import Despesa
from app.models.movimentacoes import Movimentacao
from app.models.produtos import Produto
from app.models.produtos_base import ProdutoBase
from app.models.categorias_produto import CategoriaProduto

# ajuste o import conforme seu projeto:
from app.models.mao_de_obra import MaoDeObraGrupo, MaoDeObraItem


class DashboardEventoService:
    # -------------------------
    # Helpers
    # -------------------------
    def _receita_total(self, evento: Evento) -> float:
        return float((evento.receita or 0) + (evento.receita_convite_extra or 0))

    def _key(self, s: str) -> str:
        return (s or "").strip().lower().replace(" ", "_")

    # -------------------------
    # DASH principal
    # -------------------------
    def get_dash(self, db: Session, evento_id: int) -> Optional[dict]:
        ev = (
            db.query(Evento, Cliente)
            .join(Cliente, Cliente.id == Evento.cliente_id)
            .filter(Evento.id == evento_id)
            .first()
        )
        if not ev:
            return None

        evento, cliente = ev
        receita_total = self._receita_total(evento)

        # ============================================================
        # 1) DESPESAS (pagamentos) -> agrupar por categoria
        # ============================================================
        despesas_db = (
            db.query(Despesa)
            .filter(Despesa.evento_id == evento_id)
            .order_by(Despesa.data.desc(), Despesa.id.desc())
            .all()
        )

        despesas_map: Dict[str, List[dict]] = {}
        despesas_total = 0.0

        for d in despesas_db:
            cat = (d.categoria or "Sem categoria").strip() or "Sem categoria"
            item = dict(
                id=d.id,
                data=d.data,
                descricao=d.descricao,
                categoria=cat,
                valor=float(d.valor or 0),
                fornecedor_nome=d.fornecedor_nome,
                documento_ref=d.documento_ref,
                forma_pagamento=d.forma_pagamento,
                observacao=d.observacao,
            )
            despesas_total += item["valor"]
            despesas_map.setdefault(cat, []).append(item)

        despesas_groups: List[dict] = []
        for cat, itens in sorted(
            despesas_map.items(),
            key=lambda x: sum(i["valor"] for i in x[1]),
            reverse=True,
        ):
            total_cat = float(sum(i["valor"] for i in itens))
            despesas_groups.append(
                dict(
                    key=self._key(cat),
                    label=cat,
                    total=total_cat,
                    itens=itens,
                )
            )

        # ============================================================
        # 2) CONSUMO (estoque) -> agrupar por CategoriaProduto principal
        # ============================================================
        net_qty = func.coalesce(
            func.sum(
                case(
                    (Movimentacao.tipo == "saida", Movimentacao.quantidade_base),
                    (Movimentacao.tipo == "devolucao", -Movimentacao.quantidade_base),
                    else_=0,
                )
            ),
            0,
        )
        saida_qty = func.coalesce(
            func.sum(case((Movimentacao.tipo == "saida", Movimentacao.quantidade_base), else_=0)),
            0,
        )
        devol_qty = func.coalesce(
            func.sum(case((Movimentacao.tipo == "devolucao", Movimentacao.quantidade_base), else_=0)),
            0,
        )
        cat_nome = func.coalesce(CategoriaProduto.nome, literal("Sem categoria")).label("categoria")

        consumo_rows = (
            db.query(
                Produto.id.label("produto_id"),
                Produto.nome_comercial.label("produto_nome"),
                cat_nome,
                saida_qty.label("saida_base"),
                devol_qty.label("devolucao_base"),
                func.greatest(net_qty, 0).label("consumo_base"),
                func.coalesce(
                    func.max(Movimentacao.custo_unitario),
                    Produto.custo_medio,
                    Produto.preco_reposicao,
                    0
                ).label("custo_unitario"),
            )
            .join(Movimentacao, Movimentacao.produto_id == Produto.id)
            .join(ProdutoBase, ProdutoBase.id == Produto.produto_base_id)
            .outerjoin(CategoriaProduto, CategoriaProduto.id == ProdutoBase.categoria_principal_id)
            .filter(
                Movimentacao.evento_id == evento_id,
                Movimentacao.tipo.in_(["saida", "devolucao"]),
            )
            .group_by(
                Produto.id,
                Produto.nome_comercial,
                cat_nome,
                Produto.custo_medio,
                Produto.preco_reposicao,
            )
            .order_by(func.greatest(net_qty, 0).desc(), Produto.nome_comercial.asc())
            .all()
        )

        consumo_map: Dict[str, List[dict]] = {}
        consumo_total = 0.0

        for r in consumo_rows:
            cat = (r.categoria or "Sem categoria").strip() or "Sem categoria"
            consumo_base = float(r.consumo_base or 0)
            custo_unit = float(r.custo_unitario or 0)
            custo_total = float(consumo_base * custo_unit)

            consumo_total += custo_total

            consumo_map.setdefault(cat, []).append(
                dict(
                    produto_id=int(r.produto_id),
                    produto_nome=str(r.produto_nome),
                    saida_base=float(r.saida_base or 0),
                    devolucao_base=float(r.devolucao_base or 0),
                    consumo_base=consumo_base,
                    custo_unitario=custo_unit,
                    custo_total=custo_total,
                )
            )

        consumo_groups: List[dict] = []
        for cat, itens in sorted(
            consumo_map.items(),
            key=lambda x: sum(i["custo_total"] for i in x[1]),
            reverse=True,
        ):
            total_cat = float(sum(i["custo_total"] for i in itens))
            itens_sorted = sorted(itens, key=lambda i: i["custo_total"], reverse=True)
            consumo_groups.append(
                dict(
                    key=self._key(cat),
                    categoria=cat,
                    total=total_cat,
                    itens=itens_sorted,
                )
            )

        # ============================================================
        # 3) MÃO DE OBRA -> grupos e itens
        # ============================================================
        mdo_grupos_db = (
            db.query(MaoDeObraGrupo)
            .filter(MaoDeObraGrupo.evento_id == evento_id)
            .order_by(MaoDeObraGrupo.id.asc())
            .all()
        )

        mao_de_obra_total = 0.0
        mao_de_obra_grupos: List[dict] = []

        for g in mdo_grupos_db:
            itens_db = (
                db.query(MaoDeObraItem)
                .filter(MaoDeObraItem.grupo_id == g.id)
                .order_by(MaoDeObraItem.id.asc())
                .all()
            )

            itens: List[dict] = []
            total_grupo = 0.0

            for it in itens_db:
                qt = int(it.quantidade or 0)
                vu = float(it.valor_unitario or 0)
                vt = float(it.valor_total) if it.valor_total is not None else float(qt * vu)

                total_grupo += vt
                itens.append(
                    dict(
                        id=it.id,
                        categoria=it.categoria,
                        nome=it.nome,
                        quantidade=qt,
                        valor_unitario=float(it.valor_unitario) if it.valor_unitario is not None else None,
                        valor_total=float(vt),
                        observacao=it.observacao,
                    )
                )

            mao_de_obra_total += total_grupo
            mao_de_obra_grupos.append(
                dict(
                    id=g.id,
                    nome_grupo=g.nome_grupo,
                    tipo_evento=g.tipo_evento,
                    observacao=g.observacao,
                    total=float(total_grupo),
                    itens=itens,
                )
            )

        # ============================================================
        # 4) KPIs + Charts
        # ============================================================
        custo_total = float(despesas_total + consumo_total + mao_de_obra_total)
        resultado = float(receita_total - custo_total)
        margem_pct = (resultado / receita_total) if receita_total > 0 else None

        kpis = dict(
            receita_total=float(receita_total),
            custo_total=float(custo_total),
            resultado=float(resultado),
            margem_pct=float(margem_pct) if margem_pct is not None else None,
            despesas_total=float(despesas_total),
            consumo_total=float(consumo_total),
            mao_de_obra_total=float(mao_de_obra_total),
            convidados=None,
            custo_por_pessoa=None,
        )

        waterfall = [
            dict(label="Receita", value=float(receita_total), kind="income"),
            dict(label="Despesas", value=float(-despesas_total), kind="cost"),
            dict(label="Consumo", value=float(-consumo_total), kind="cost"),
            dict(label="Mão de obra", value=float(-mao_de_obra_total), kind="cost"),
            dict(label="Resultado", value=float(resultado), kind="result"),
        ]

        distribuicao_custos = [
            dict(label="Buffet / Consumo", value=float(consumo_total)),
            dict(label="Despesas", value=float(despesas_total)),
            dict(label="Mão de obra", value=float(mao_de_obra_total)),
        ]

        # Top 5 para “insights rápidos”
        top_despesas = [
            dict(label=g["label"], value=g["total"]) for g in despesas_groups[:5]
        ]
        top_consumo = [
            dict(label=g["categoria"], value=g["total"]) for g in consumo_groups[:5]
        ]
        top_mao = [
            dict(label=g["nome_grupo"], value=g["total"]) for g in sorted(mao_de_obra_grupos, key=lambda x: x["total"], reverse=True)[:5]
        ]

        charts = dict(
            waterfall=waterfall,
            distribuicao_custos=distribuicao_custos,
            custo_por_dia=[],
            consumo_por_dia=[],
            despesas_por_dia=[],
        )

        header = dict(
            evento_id=evento.id,
            nome=evento.nome,
            cliente_id=cliente.id,
            cliente_nome=cliente.nome,
            data_inicio=evento.data_inicio,
            data_fim=evento.data_fim,
            status=evento.status,
            local_evento=evento.local_evento,
        )

        return dict(
            meta=dict(moeda="BRL", gerado_em=datetime.utcnow()),
            header=header,
            kpis=kpis,
            charts=charts,
            sections=dict(
                despesas=despesas_groups,
                consumo=consumo_groups,
                mao_de_obra=mao_de_obra_grupos,
            ),
            resumo=dict(
                top_despesas=top_despesas,
                top_consumo=top_consumo,
                top_mao_de_obra=top_mao,
            ),
        )