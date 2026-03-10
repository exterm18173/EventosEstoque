from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_, literal, true

from app.models.eventos import Evento
from app.models.clientes import Cliente
from app.models.despesas import Despesa
from app.models.movimentacoes import Movimentacao
from app.models.produtos import Produto
from app.models.produtos_base import ProdutoBase
from app.models.categorias_produto import CategoriaProduto


class DashboardEventosService:
    # =========================
    # Helpers
    # =========================
    def _receita_expr(self):
        return func.coalesce(Evento.receita, 0) + func.coalesce(Evento.receita_convite_extra, 0)

    def _eventos_range_filter(self, from_: Optional[date], to: Optional[date]):
        # filtro por “sobreposição” do período do evento com o range
        conds = []
        if from_ is not None:
            conds.append(Evento.data_fim >= from_)
        if to is not None:
            conds.append(Evento.data_inicio <= to)
        return and_(*conds) if conds else true()

    def _apply_filters(
        self,
        query,
        from_: Optional[date],
        to: Optional[date],
        status: Optional[str],
        q: Optional[str],
    ):
        query = query.filter(self._eventos_range_filter(from_, to))

        if status and status.strip():
            query = query.filter(Evento.status == status.strip())

        if q and q.strip():
            s = f"%{q.strip()}%"
            query = query.filter(or_(Evento.nome.ilike(s), Cliente.nome.ilike(s)))

        return query

    # =========================
    # Resumo (lista + total + kpis globais)
    # =========================
    def resumo(
        self,
        db: Session,
        from_: Optional[date],
        to: Optional[date],
        status: Optional[str],
        q: Optional[str],
        limit: int = 50,
        offset: int = 0,
    ):
        receita = self._receita_expr()

        # ---- despesas por evento (subquery) ----
        despesas_sq = (
            db.query(
                Despesa.evento_id.label("evento_id"),
                func.coalesce(func.sum(Despesa.valor), 0).label("despesas_total"),
            )
            .filter(Despesa.evento_id.isnot(None))
            .group_by(Despesa.evento_id)
            .subquery()
        )

        # ---- consumo por evento (subquery) ----
        # 1) net_qty por (evento, produto) = sum(saida) - sum(devolucao)
        net_qty_sq = (
            db.query(
                Movimentacao.evento_id.label("evento_id"),
                Movimentacao.produto_id.label("produto_id"),
                func.coalesce(
                    func.sum(
                        case(
                            (Movimentacao.tipo == "saida", Movimentacao.quantidade_base),
                            (Movimentacao.tipo == "devolucao", -Movimentacao.quantidade_base),
                            else_=0,
                        )
                    ),
                    0,
                ).label("net_qty"),
                func.coalesce(func.max(Movimentacao.custo_unitario), 0).label("mov_custo_unit"),
            )
            .filter(
                Movimentacao.evento_id.isnot(None),
                Movimentacao.tipo.in_(["saida", "devolucao"]),
            )
            .group_by(Movimentacao.evento_id, Movimentacao.produto_id)
            .subquery()
        )

        # 2) custo_unit = mov_custo_unit OR produto.custo_medio OR produto.preco_reposicao OR 0
        custo_unit = func.coalesce(
            net_qty_sq.c.mov_custo_unit,
            Produto.custo_medio,
            Produto.preco_reposicao,
            0,
        )

        # 3) consumo_total por evento = sum(greatest(net_qty,0) * custo_unit)
        consumo_sq = (
            db.query(
                net_qty_sq.c.evento_id.label("evento_id"),
                func.coalesce(
                    func.sum(func.greatest(net_qty_sq.c.net_qty, 0) * custo_unit),
                    0,
                ).label("consumo_total"),
            )
            .join(Produto, Produto.id == net_qty_sq.c.produto_id)
            .group_by(net_qty_sq.c.evento_id)
            .subquery()
        )

        # ---- base query eventos (sem paginação) ----
        base = (
            db.query(
                Evento.id.label("evento_id"),
                Evento.nome.label("nome"),
                Evento.data_inicio,
                Evento.data_fim,
                Evento.status,
                Cliente.id.label("cliente_id"),
                Cliente.nome.label("cliente_nome"),
                receita.label("receita"),
                func.coalesce(despesas_sq.c.despesas_total, 0).label("despesas_total"),
                func.coalesce(consumo_sq.c.consumo_total, 0).label("consumo_total"),
            )
            .join(Cliente, Cliente.id == Evento.cliente_id)
            .outerjoin(despesas_sq, despesas_sq.c.evento_id == Evento.id)
            .outerjoin(consumo_sq, consumo_sq.c.evento_id == Evento.id)
        )

        base = self._apply_filters(base, from_, to, status, q)

        # ---- total_items (COUNT sem paginação) ----
        count_q = db.query(func.count(Evento.id)).join(Cliente, Cliente.id == Evento.cliente_id)
        count_q = self._apply_filters(count_q, from_, to, status, q)
        total_items = int(count_q.scalar() or 0)

        # ---- KPIs globais (sem paginação) ----
        # soma de receita, despesas e consumo no conjunto filtrado
        agg = base.with_entities(
            func.count(literal(1)).label("eventos"),
            func.coalesce(func.sum(receita), 0).label("receita_total"),
            func.coalesce(func.sum(func.coalesce(despesas_sq.c.despesas_total, 0)), 0).label("despesas_total"),
            func.coalesce(func.sum(func.coalesce(consumo_sq.c.consumo_total, 0)), 0).label("consumo_total"),
        ).first()

        receita_total = float(agg.receita_total or 0)
        despesas_total = float(agg.despesas_total or 0)
        consumo_total = float(agg.consumo_total or 0)
        custo_total = despesas_total + consumo_total
        resultado_total = receita_total - custo_total

        kpis = dict(
            eventos=int(agg.eventos or 0),
            receita_total=receita_total,
            despesas_total=despesas_total,
            consumo_total=consumo_total,
            custo_total=float(custo_total),
            resultado_total=float(resultado_total),
        )

        # ---- lista paginada ----
        paged = (
            base.order_by(Evento.data_inicio.desc(), Evento.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        # monta resposta (custo_total e resultado no Python)
        eventos = []
        for r in paged:
            despesas_v = float(r.despesas_total or 0)
            consumo_v = float(r.consumo_total or 0)
            receita_v = float(r.receita or 0)
            custo_v = despesas_v + consumo_v
            resultado_v = receita_v - custo_v

            eventos.append(
                dict(
                    evento_id=r.evento_id,
                    nome=r.nome,
                    cliente_id=r.cliente_id,
                    cliente_nome=r.cliente_nome,
                    data_inicio=r.data_inicio,
                    data_fim=r.data_fim,
                    status=r.status,
                    receita=receita_v,
                    despesas_total=despesas_v,
                    consumo_total=consumo_v,
                    custo_total=custo_v,
                    resultado=resultado_v,
                )
            )

        return total_items, kpis, eventos

    # =========================
    # Detalhe (1 evento)
    # =========================
    def detalhe(self, db: Session, evento_id: int):
        ev = (
            db.query(Evento, Cliente)
            .join(Cliente, Cliente.id == Evento.cliente_id)
            .filter(Evento.id == evento_id)
            .first()
        )
        if not ev:
            return None

        evento, cliente = ev
        receita = float((evento.receita or 0) + (evento.receita_convite_extra or 0))

        # -------------------------
        # despesas item-a-item
        # -------------------------
        despesas_rows = (
            db.query(Despesa)
            .filter(Despesa.evento_id == evento_id)
            .order_by(Despesa.data.desc(), Despesa.id.desc())
            .all()
        )

        despesas = [
            dict(
                id=d.id,
                data=d.data,
                descricao=d.descricao,
                categoria=d.categoria,
                valor=float(d.valor),
                fornecedor_nome=d.fornecedor_nome,
                documento_ref=d.documento_ref,
                forma_pagamento=d.forma_pagamento,
            )
            for d in despesas_rows
        ]
        despesas_total = float(sum(x["valor"] for x in despesas))

        # -------------------------
        # consumo agrupado por produto
        # -------------------------
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

        rows = (
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
                    0,
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

        consumo_itens = []
        consumo_total = 0.0
        for r in rows:
            consumo_base = float(r.consumo_base or 0)
            custo_unit = float(r.custo_unitario or 0)
            custo_total = consumo_base * custo_unit
            consumo_total += custo_total

            consumo_itens.append(
                dict(
                    produto_id=r.produto_id,
                    produto_nome=r.produto_nome,
                    categoria=r.categoria,
                    saida_base=float(r.saida_base or 0),
                    devolucao_base=float(r.devolucao_base or 0),
                    consumo_base=consumo_base,
                    custo_unitario=custo_unit,
                    custo_total=float(custo_total),
                )
            )

        # -------------------------
        # por categoria (unificado)
        # -------------------------
        desp_cat = func.coalesce(Despesa.categoria, literal("Sem categoria")).label("categoria")
        desp_total = func.coalesce(func.sum(Despesa.valor), 0).label("total")

        despesas_cat = (
            db.query(desp_cat, desp_total)
            .filter(Despesa.evento_id == evento_id)
            .group_by(desp_cat)
            .order_by(func.sum(Despesa.valor).desc())
            .all()
        )

        por_categoria = []
        for c in despesas_cat:
            por_categoria.append({"tipo": "despesa", "categoria": c.categoria, "total": float(c.total)})

        consumo_map: dict[str, float] = {}
        for it in consumo_itens:
            k = (it["categoria"] or "Sem categoria")
            consumo_map[k] = consumo_map.get(k, 0.0) + float(it["custo_total"])

        for cat, tot in sorted(consumo_map.items(), key=lambda x: x[1], reverse=True):
            por_categoria.append({"tipo": "consumo", "categoria": cat, "total": float(tot)})

        custo_total = despesas_total + consumo_total
        resultado = receita - custo_total

        return dict(
            evento_id=evento.id,
            nome=evento.nome,
            cliente_id=cliente.id,
            cliente_nome=cliente.nome,
            data_inicio=evento.data_inicio,
            data_fim=evento.data_fim,
            status=evento.status,
            receita=receita,
            despesas_total=float(despesas_total),
            consumo_total=float(consumo_total),
            custo_total=float(custo_total),
            resultado=float(resultado),
            por_categoria=por_categoria,
            despesas=despesas,
            consumo_itens=consumo_itens,
        )