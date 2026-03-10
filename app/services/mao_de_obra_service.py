from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.mao_de_obra import MaoDeObraGrupo, MaoDeObraItem
from app.schemas.mao_de_obra import MaoDeObraInput, MaoDeObraAppendInput, MaoDeObraItemUpdate


class MaoDeObraService:
    # ---------- helpers ----------
    def _calc_valor_total(
        self,
        quantidade: int,
        valor_unitario: Decimal | None,
        valor_total: Decimal | None,
    ) -> Decimal | None:
        # Se vier valor_total, respeita.
        if valor_total is not None:
            return valor_total

        # Se não vier, tenta calcular.
        if valor_unitario is None:
            return None

        return (Decimal(quantidade) * Decimal(valor_unitario)).quantize(Decimal("0.01"))

    def _find_grupo(
        self,
        db: Session,
        evento_id: int,
        nome_grupo: str,
        tipo_evento: str | None,
    ) -> MaoDeObraGrupo | None:
        # Estratégia: considera "mesmo grupo" por (evento_id + nome_grupo + tipo_evento)
        # Se você quiser considerar só nome_grupo, é só remover tipo_evento do filtro.
        return (
            db.query(MaoDeObraGrupo)
            .filter(
                MaoDeObraGrupo.evento_id == evento_id,
                MaoDeObraGrupo.nome_grupo == nome_grupo,
                MaoDeObraGrupo.tipo_evento.is_(tipo_evento) if tipo_evento is None else MaoDeObraGrupo.tipo_evento == tipo_evento,
            )
            .first()
        )

    # ---------- REPLACE TOTAL (o seu upsert atual) ----------
    def upsert_evento(self, db: Session, payload: MaoDeObraInput) -> list[MaoDeObraGrupo]:
        try:
            db.query(MaoDeObraGrupo).filter(MaoDeObraGrupo.evento_id == payload.evento_id).delete()
            db.flush()

            for g in payload.lista_de_grupos:
                grupo = MaoDeObraGrupo(
                    evento_id=payload.evento_id,
                    nome_grupo=g.nome_grupo,
                    tipo_evento=g.tipo_evento,
                    observacao=g.observacao,
                )
                db.add(grupo)
                db.flush()

                for it in g.subitens:
                    valor_total = self._calc_valor_total(
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=it.valor_total,
                    )

                    item = MaoDeObraItem(
                        grupo_id=grupo.id,
                        categoria=it.categoria,
                        nome=it.nome,
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=valor_total,
                        observacao=it.observacao,
                    )
                    db.add(item)

            db.commit()

            return (
                db.query(MaoDeObraGrupo)
                .filter(MaoDeObraGrupo.evento_id == payload.evento_id)
                .all()
            )
        except Exception:
            db.rollback()
            raise

    # ---------- APPEND EM LOTE (NOVO) ----------
    def append_evento(self, db: Session, evento_id: int, payload: MaoDeObraAppendInput) -> list[MaoDeObraGrupo]:
        """
        Adiciona grupos/subitens ao evento sem apagar o que existe.
        - Se o grupo (nome_grupo+tipo_evento) já existir no evento: atualiza campos opcionais e adiciona itens.
        - Se não existir: cria o grupo e adiciona itens.
        """
        try:
            for g in payload.lista_de_grupos:
                grupo = self._find_grupo(db, evento_id, g.nome_grupo, g.tipo_evento)

                if grupo is None:
                    grupo = MaoDeObraGrupo(
                        evento_id=evento_id,
                        nome_grupo=g.nome_grupo,
                        tipo_evento=g.tipo_evento,
                        observacao=g.observacao,
                    )
                    db.add(grupo)
                    db.flush()
                else:
                    # Se quiser manter observacao antiga quando vier None:
                    if g.observacao is not None:
                        grupo.observacao = g.observacao
                    # opcional: se quiser atualizar tipo_evento / nome_grupo, cuidado com a "chave" de match.
                    # aqui a gente não altera pra evitar bagunçar o match.

                for it in g.subitens:
                    valor_total = self._calc_valor_total(
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=it.valor_total,
                    )

                    item = MaoDeObraItem(
                        grupo_id=grupo.id,
                        categoria=it.categoria,
                        nome=it.nome,
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=valor_total,
                        observacao=it.observacao,
                    )
                    db.add(item)

            db.commit()

            # reload
            return (
                db.query(MaoDeObraGrupo)
                .filter(MaoDeObraGrupo.evento_id == evento_id)
                .all()
            )
        except Exception:
            db.rollback()
            raise

    # ---------- GETS ----------
    def get_evento(self, db: Session, evento_id: int) -> list[MaoDeObraGrupo]:
        return (
            db.query(MaoDeObraGrupo)
            .filter(MaoDeObraGrupo.evento_id == evento_id)
            .all()
        )

    def update_item(self, db: Session, item_id: int, payload: MaoDeObraItemUpdate) -> MaoDeObraItem:
        item = db.get(MaoDeObraItem, item_id)
        if not item:
            raise ValueError("Item não encontrado")

        item.categoria = payload.categoria
        item.nome = payload.nome
        item.quantidade = payload.quantidade
        item.valor_unitario = payload.valor_unitario
        item.valor_total = self._calc_valor_total(payload.quantidade, payload.valor_unitario, payload.valor_total)
        item.observacao = payload.observacao

        db.commit()
        db.refresh(item)
        return item

    def delete_item(self, db: Session, item_id: int) -> None:
        item = db.get(MaoDeObraItem, item_id)
        if not item:
            return
        db.delete(item)
        db.commit()

    # ---------- TOTAIS ----------
    def total_evento(self, db: Session, evento_id: int) -> float:
        total = (
            db.query(func.coalesce(func.sum(MaoDeObraItem.valor_total), 0))
            .join(MaoDeObraGrupo, MaoDeObraGrupo.id == MaoDeObraItem.grupo_id)
            .filter(MaoDeObraGrupo.evento_id == evento_id)
            .scalar()
        )
        return float(total or 0)

    def por_categoria(self, db: Session, evento_id: int) -> list[dict]:
        rows = (
            db.query(
                func.coalesce(MaoDeObraItem.categoria, "Sem categoria").label("categoria"),
                func.coalesce(func.sum(MaoDeObraItem.valor_total), 0).label("total"),
            )
            .join(MaoDeObraGrupo, MaoDeObraGrupo.id == MaoDeObraItem.grupo_id)
            .filter(MaoDeObraGrupo.evento_id == evento_id)
            .group_by(func.coalesce(MaoDeObraItem.categoria, "Sem categoria"))
            .order_by(func.sum(MaoDeObraItem.valor_total).desc())
            .all()
        )
        return [{"categoria": r.categoria, "total": float(r.total)} for r in rows]
