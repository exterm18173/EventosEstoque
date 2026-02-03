from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models.estoque_saldos import EstoqueSaldo
from app.models.produtos import Produto
from app.models.locais import Local
from app.models.movimentacoes import Movimentacao
from app.models.despesas import Despesa
from app.models.eventos import Evento


class RelatoriosService:
    def estoque(
        self,
        db: Session,
        *,
        produto_id: int | None = None,
        local_id: int | None = None,
        somente_positivos: bool = False,
    ):
        stmt = (
            select(
                EstoqueSaldo.produto_id,
                Produto.nome_comercial.label("produto_nome"),
                EstoqueSaldo.local_id,
                Local.nome.label("local_nome"),
                EstoqueSaldo.quantidade_base,
            )
            .join(Produto, Produto.id == EstoqueSaldo.produto_id)
            .join(Local, Local.id == EstoqueSaldo.local_id)
        )

        if produto_id is not None:
            stmt = stmt.where(EstoqueSaldo.produto_id == produto_id)
        if local_id is not None:
            stmt = stmt.where(EstoqueSaldo.local_id == local_id)
        if somente_positivos:
            stmt = stmt.where(EstoqueSaldo.quantidade_base > 0)

        stmt = stmt.order_by(Produto.nome_comercial.asc(), Local.nome.asc())
        return db.execute(stmt).all()

    def movimentacoes(
        self,
        db: Session,
        *,
        data_inicio: str | None = None,  # YYYY-MM-DD
        data_fim: str | None = None,
        tipo: str | None = None,         # entrada|saida|transferencia|ajuste
        origem: str | None = None,       # compra|uso_evento|aluguel|inventario|xml...
        produto_id: int | None = None,
        evento_id: int | None = None,
        aluguel_id: int | None = None,
        local_id: int | None = None,     # filtra origem OU destino
        limit: int = 300,
    ):
        stmt = (
            select(
                Movimentacao.id,
                Movimentacao.created_at,
                Movimentacao.tipo,
                Movimentacao.origem,
                Movimentacao.produto_id,
                Produto.nome_comercial.label("produto_nome"),
                Movimentacao.quantidade_informada,
                Movimentacao.unidade_informada_id,
                Movimentacao.fator_para_base,
                Movimentacao.quantidade_base,
                Movimentacao.custo_unitario,
                Movimentacao.evento_id,
                Movimentacao.aluguel_id,
                Movimentacao.local_origem_id,
                Movimentacao.local_destino_id,
            )
            .join(Produto, Produto.id == Movimentacao.produto_id)
        )

        if data_inicio:
            stmt = stmt.where(Movimentacao.created_at >= data_inicio)
        if data_fim:
            stmt = stmt.where(Movimentacao.created_at <= data_fim)

        if tipo:
            stmt = stmt.where(Movimentacao.tipo == tipo)
        if origem:
            stmt = stmt.where(Movimentacao.origem == origem)

        if produto_id is not None:
            stmt = stmt.where(Movimentacao.produto_id == produto_id)
        if evento_id is not None:
            stmt = stmt.where(Movimentacao.evento_id == evento_id)
        if aluguel_id is not None:
            stmt = stmt.where(Movimentacao.aluguel_id == aluguel_id)

        if local_id is not None:
            stmt = stmt.where(
                (Movimentacao.local_origem_id == local_id) | (Movimentacao.local_destino_id == local_id)
            )

        stmt = stmt.order_by(Movimentacao.created_at.desc()).limit(limit)
        return db.execute(stmt).all()

    def custo_evento(self, db: Session, evento_id: int):
        if not db.get(Evento, evento_id):
            raise ValueError("Evento não encontrado.")

        despesas_total = db.execute(
            select(func.coalesce(func.sum(Despesa.valor), 0.0)).where(Despesa.evento_id == evento_id)
        ).scalar_one()

        # consumo de estoque: saídas com evento_id
        consumo_total = db.execute(
            select(
                func.coalesce(
                    func.sum(
                        func.coalesce(Movimentacao.quantidade_base, 0.0) * func.coalesce(Movimentacao.custo_unitario, 0.0)
                    ),
                    0.0,
                )
            ).where(and_(Movimentacao.evento_id == evento_id, Movimentacao.tipo == "saida"))
        ).scalar_one()

        total = float(despesas_total or 0.0) + float(consumo_total or 0.0)
        return float(despesas_total or 0.0), float(consumo_total or 0.0), float(total)
