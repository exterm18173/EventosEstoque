from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.mao_de_obra import MaoDeObraGrupo
from app.models.mao_de_obra_modelo import (
    MaoDeObraModelo,
    MaoDeObraModeloGrupo,
    MaoDeObraModeloItem,
)

from app.schemas.mao_de_obra import MaoDeObraInput, MaoDeObraAppendInput
from app.schemas.mao_de_obra_modelos import (
    MaoDeObraModeloCreate,
    MaoDeObraModeloReplace,
    MaoDeObraModeloFromEventoInput,
    AplicarModeloPayload,
)

from app.services.mao_de_obra_service import MaoDeObraService


class MaoDeObraModelosService:
    def __init__(self) -> None:
        self.evento_service = MaoDeObraService()

    def _calc_valor_total(self, quantidade: int, valor_unitario: Decimal | None, valor_total: Decimal | None) -> Decimal | None:
        if valor_total is not None:
            return valor_total
        if valor_unitario is None:
            return None
        return (Decimal(quantidade) * Decimal(valor_unitario)).quantize(Decimal("0.01"))

    def _get_modelo_or_404(self, db: Session, modelo_id: int) -> MaoDeObraModelo:
        modelo = db.get(MaoDeObraModelo, modelo_id)
        if not modelo:
            raise ValueError("Modelo não encontrado")
        return modelo

    def _nome_em_uso(self, db: Session, nome: str, ignore_modelo_id: int | None = None) -> bool:
        q = db.query(MaoDeObraModelo).filter(MaoDeObraModelo.nome == nome)
        if ignore_modelo_id is not None:
            q = q.filter(MaoDeObraModelo.id != ignore_modelo_id)
        return db.query(q.exists()).scalar() is True

    def list_modelos(self, db: Session, tipo_evento: str | None = None) -> list[MaoDeObraModelo]:
        q = db.query(MaoDeObraModelo)
        if tipo_evento is not None and tipo_evento.strip() != "":
            q = q.filter(MaoDeObraModelo.tipo_evento == tipo_evento)
        return q.order_by(MaoDeObraModelo.nome.asc()).all()

    def get_modelo(self, db: Session, modelo_id: int) -> MaoDeObraModelo:
        return self._get_modelo_or_404(db, modelo_id)

    def create_modelo(self, db: Session, payload: MaoDeObraModeloCreate) -> MaoDeObraModelo:
        if self._nome_em_uso(db, payload.nome):
            raise ValueError("Já existe um modelo com esse nome")

        try:
            modelo = MaoDeObraModelo(
                nome=payload.nome,
                tipo_evento=payload.tipo_evento,
                observacao=payload.observacao,
            )
            db.add(modelo)
            db.flush()

            for g in payload.lista_de_grupos:
                mg = MaoDeObraModeloGrupo(
                    modelo_id=modelo.id,
                    nome_grupo=g.nome_grupo,
                    tipo_evento=g.tipo_evento,
                    observacao=g.observacao,
                )
                db.add(mg)
                db.flush()

                for it in g.subitens:
                    valor_total = self._calc_valor_total(it.quantidade, it.valor_unitario, it.valor_total)
                    mi = MaoDeObraModeloItem(
                        grupo_id=mg.id,
                        categoria=it.categoria,
                        nome=it.nome,
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=valor_total,
                        observacao=it.observacao,
                    )
                    db.add(mi)

            db.commit()
            db.refresh(modelo)
            return modelo
        except Exception:
            db.rollback()
            raise

    def replace_modelo(self, db: Session, modelo_id: int, payload: MaoDeObraModeloReplace) -> MaoDeObraModelo:
        modelo = self._get_modelo_or_404(db, modelo_id)

        if self._nome_em_uso(db, payload.nome, ignore_modelo_id=modelo_id):
            raise ValueError("Já existe outro modelo com esse nome")

        try:
            modelo.nome = payload.nome
            modelo.tipo_evento = payload.tipo_evento
            modelo.observacao = payload.observacao

            db.query(MaoDeObraModeloGrupo).filter(MaoDeObraModeloGrupo.modelo_id == modelo_id).delete()
            db.flush()

            for g in payload.lista_de_grupos:
                mg = MaoDeObraModeloGrupo(
                    modelo_id=modelo.id,
                    nome_grupo=g.nome_grupo,
                    tipo_evento=g.tipo_evento,
                    observacao=g.observacao,
                )
                db.add(mg)
                db.flush()

                for it in g.subitens:
                    valor_total = self._calc_valor_total(it.quantidade, it.valor_unitario, it.valor_total)
                    mi = MaoDeObraModeloItem(
                        grupo_id=mg.id,
                        categoria=it.categoria,
                        nome=it.nome,
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=valor_total,
                        observacao=it.observacao,
                    )
                    db.add(mi)

            db.commit()
            db.refresh(modelo)
            return modelo
        except Exception:
            db.rollback()
            raise

    def delete_modelo(self, db: Session, modelo_id: int) -> None:
        modelo = self._get_modelo_or_404(db, modelo_id)
        db.delete(modelo)
        db.commit()

    def create_from_evento(self, db: Session, evento_id: int, payload: MaoDeObraModeloFromEventoInput) -> MaoDeObraModelo:
        if self._nome_em_uso(db, payload.nome):
            raise ValueError("Já existe um modelo com esse nome")

        try:
            grupos_evento = db.query(MaoDeObraGrupo).filter(MaoDeObraGrupo.evento_id == evento_id).all()

            modelo = MaoDeObraModelo(
                nome=payload.nome,
                tipo_evento=payload.tipo_evento,
                observacao=payload.observacao,
            )
            db.add(modelo)
            db.flush()

            for g in grupos_evento:
                mg = MaoDeObraModeloGrupo(
                    modelo_id=modelo.id,
                    nome_grupo=g.nome_grupo,
                    tipo_evento=g.tipo_evento,
                    observacao=g.observacao,
                )
                db.add(mg)
                db.flush()

                for it in g.subitens:
                    mi = MaoDeObraModeloItem(
                        grupo_id=mg.id,
                        categoria=it.categoria,
                        nome=it.nome,
                        quantidade=it.quantidade,
                        valor_unitario=it.valor_unitario,
                        valor_total=it.valor_total,
                        observacao=it.observacao,
                    )
                    db.add(mi)

            db.commit()
            db.refresh(modelo)
            return modelo
        except Exception:
            db.rollback()
            raise

    def apply_modelo(self, db: Session, evento_id: int, modelo_id: int, payload: AplicarModeloPayload):
        modelo = self._get_modelo_or_404(db, modelo_id)

        mode = (payload.mode or "append").strip().lower()
        if mode not in ("append", "replace"):
            raise ValueError('mode inválido. Use "append" ou "replace".')

        overrides = {o.item_modelo_id: o.quantidade for o in payload.overrides}

        lista_de_grupos = []
        for g in modelo.grupos:
            subitens = []
            for it in g.itens:
                qtd = overrides.get(it.id, it.quantidade)
                valor_total = self._calc_valor_total(qtd, it.valor_unitario, it.valor_total)

                subitens.append(
                    {
                        "categoria": it.categoria,
                        "nome": it.nome,
                        "quantidade": qtd,
                        "valor_unitario": it.valor_unitario,
                        "valor_total": valor_total,
                        "observacao": it.observacao,
                    }
                )

            lista_de_grupos.append(
                {
                    "nome_grupo": g.nome_grupo,
                    "tipo_evento": g.tipo_evento,
                    "observacao": g.observacao,
                    "subitens": subitens,
                }
            )

        if mode == "replace":
            up = MaoDeObraInput(evento_id=evento_id, lista_de_grupos=lista_de_grupos)
            return self.evento_service.upsert_evento(db, up)
        else:
            ap = MaoDeObraAppendInput(lista_de_grupos=lista_de_grupos)
            return self.evento_service.append_evento(db, evento_id, ap)
