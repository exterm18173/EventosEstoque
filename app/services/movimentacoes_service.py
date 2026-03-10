from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.movimentacoes import Movimentacao
from app.models.produtos import Produto
from app.models.unidades import Unidade
from app.models.locais import Local
from app.models.lotes import Lote
from app.models.estoque_saldos import EstoqueSaldo
from app.models.setores_consumo import SetorConsumo

from app.schemas.movimentacoes_crud import MovimentacaoCreate

TIPOS_VALIDOS = {"entrada", "saida", "transferencia", "ajuste", "devolucao"}


class MovimentacoesService:
    # =========================
    # LIST / GET
    # =========================
    def list(
        self,
        db: Session,
        *,
        produto_id: int | None = None,
        evento_id: int | None = None,
        aluguel_id: int | None = None,
        setor_consumo_id: int | None = None,
        tipo: str | None = None,
        origem: str | None = None,
        local_id: int | None = None,
        data_inicio: str | None = None,  # YYYY-MM-DD
        data_fim: str | None = None,     # YYYY-MM-DD
    ) -> list[Movimentacao]:
        stmt = select(Movimentacao)

        if produto_id is not None:
            stmt = stmt.where(Movimentacao.produto_id == produto_id)

        if evento_id is not None:
            stmt = stmt.where(Movimentacao.evento_id == evento_id)

        if aluguel_id is not None:
            stmt = stmt.where(Movimentacao.aluguel_id == aluguel_id)

        if setor_consumo_id is not None:
            stmt = stmt.where(Movimentacao.setor_consumo_id == setor_consumo_id)

        if tipo is not None:
            stmt = stmt.where(Movimentacao.tipo == tipo)

        if origem is not None:
            stmt = stmt.where(Movimentacao.origem == origem)

        if local_id is not None:
            stmt = stmt.where(
                (Movimentacao.local_origem_id == local_id)
                | (Movimentacao.local_destino_id == local_id)
            )

        if data_inicio:
            dt_ini = datetime.fromisoformat(f"{data_inicio}T00:00:00")
            stmt = stmt.where(Movimentacao.created_at >= dt_ini)

        if data_fim:
            dt_fim = datetime.fromisoformat(f"{data_fim}T23:59:59")
            stmt = stmt.where(Movimentacao.created_at <= dt_fim)

        stmt = stmt.order_by(Movimentacao.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, mov_id: int) -> Movimentacao:
        mov = db.get(Movimentacao, mov_id)
        if not mov:
            raise ValueError("Movimentação não encontrada.")
        return mov

    # =========================
    # CREATE (1 item)
    # =========================
    def create(self, db: Session, data: MovimentacaoCreate) -> Movimentacao:
        return self.create_one(db, data, commit=True)

    # =========================
    # CREATE ONE (usado por batch)
    # =========================
    def create_one(
        self,
        db: Session,
        data: MovimentacaoCreate,
        *,
        commit: bool,
    ) -> Movimentacao:
        if data.tipo not in TIPOS_VALIDOS:
            raise ValueError(
                f"Tipo inválido. Use: {', '.join(sorted(TIPOS_VALIDOS))}."
            )

        produto = db.get(Produto, data.produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")

        unidade = db.get(Unidade, data.unidade_informada_id)
        if not unidade:
            raise ValueError("Unidade informada inválida.")

        # -------------------------
        # SETOR DE CONSUMO
        # -------------------------
        if data.setor_consumo_id is not None:
            setor = db.get(SetorConsumo, data.setor_consumo_id)
            if not setor:
                raise ValueError("Setor de consumo inválido.")
            if not setor.ativo:
                raise ValueError("Setor de consumo inativo.")

        # regra alinhada com o front:
        # apenas saída vinculada a evento exige setor
        if data.tipo == "saida" and data.evento_id is not None:
            if data.setor_consumo_id is None:
                raise ValueError("Saída vinculada a evento exige setor_consumo_id.")

        # -------------------------
        # LOCAIS EXIGIDOS POR TIPO
        # -------------------------
        if data.tipo in {"entrada", "devolucao"}:
            if data.local_destino_id is None:
                raise ValueError("Entrada/Devolução exige local_destino_id.")

            if not db.get(Local, data.local_destino_id):
                raise ValueError("Local destino inválido.")

        elif data.tipo == "saida":
            if data.local_origem_id is None:
                raise ValueError("Saída exige local_origem_id.")

            if not db.get(Local, data.local_origem_id):
                raise ValueError("Local origem inválido.")

        elif data.tipo == "transferencia":
            if data.local_origem_id is None or data.local_destino_id is None:
                raise ValueError(
                    "Transferência exige local_origem_id e local_destino_id."
                )

            if data.local_origem_id == data.local_destino_id:
                raise ValueError("Transferência exige locais diferentes.")

            if not db.get(Local, data.local_origem_id):
                raise ValueError("Local origem inválido.")

            if not db.get(Local, data.local_destino_id):
                raise ValueError("Local destino inválido.")

        elif data.tipo == "ajuste":
            if data.local_origem_id is None and data.local_destino_id is None:
                raise ValueError(
                    "Ajuste exige local_origem_id (redução) ou local_destino_id (aumento)."
                )

            if data.local_origem_id is not None and not db.get(Local, data.local_origem_id):
                raise ValueError("Local origem inválido.")

            if data.local_destino_id is not None and not db.get(Local, data.local_destino_id):
                raise ValueError("Local destino inválido.")

        # -------------------------
        # LOTE
        # -------------------------
        if produto.controla_lote:
            if data.tipo in {"entrada", "saida", "transferencia", "devolucao", "ajuste"}:
                if data.lote_id is None:
                    raise ValueError("Produto controla lote: informe lote_id.")

            if data.lote_id is not None:
                lote = db.get(Lote, data.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")
                if lote.produto_id != produto.id:
                    raise ValueError("Lote não pertence a este produto.")

        # -------------------------
        # CÁLCULO BASE
        # -------------------------
        quantidade_base = float(data.quantidade_informada) * float(data.fator_para_base)

        # -------------------------
        # VALIDA SALDO (somente quando reduz)
        # -------------------------
        if data.tipo == "saida":
            self._assert_saldo(db, produto.id, data.local_origem_id, quantidade_base)

        elif data.tipo == "transferencia":
            self._assert_saldo(db, produto.id, data.local_origem_id, quantidade_base)

        elif data.tipo == "ajuste" and data.local_origem_id is not None:
            self._assert_saldo(db, produto.id, data.local_origem_id, quantidade_base)

        # lote também precisa de saldo nas operações de redução
        if produto.controla_lote and data.lote_id is not None:
            lote = db.get(Lote, data.lote_id)
            if not lote:
                raise ValueError("Lote inválido.")

            if data.tipo == "saida":
                if lote.local_id != data.local_origem_id:
                    raise ValueError("Lote deve estar no mesmo local de origem na saída.")
                if float(lote.quantidade_base_atual) < quantidade_base - 1e-9:
                    raise ValueError("Saldo insuficiente no lote.")

            elif data.tipo == "transferencia":
                if lote.local_id != data.local_origem_id:
                    raise ValueError("Lote deve estar no local de origem para transferir.")
                if float(lote.quantidade_base_atual) < quantidade_base - 1e-9:
                    raise ValueError("Saldo insuficiente no lote para transferência.")

            elif data.tipo == "ajuste" and data.local_origem_id is not None:
                if lote.local_id != data.local_origem_id:
                    raise ValueError("Lote deve estar no local de origem para ajuste de redução.")
                if float(lote.quantidade_base_atual) < quantidade_base - 1e-9:
                    raise ValueError("Saldo insuficiente no lote para ajuste.")

        # -------------------------
        # CRIA MOVIMENTAÇÃO
        # -------------------------
        mov = Movimentacao(
            produto_id=data.produto_id,
            evento_id=data.evento_id,
            aluguel_id=data.aluguel_id,
            usuario_id=data.usuario_id,
            setor_consumo_id=data.setor_consumo_id,
            tipo=data.tipo,
            quantidade_informada=float(data.quantidade_informada),
            unidade_informada_id=data.unidade_informada_id,
            fator_para_base=float(data.fator_para_base),
            quantidade_base=quantidade_base,
            custo_unitario=data.custo_unitario,
            local_origem_id=data.local_origem_id,
            local_destino_id=data.local_destino_id,
            lote_id=data.lote_id,
            embalagem_id=data.embalagem_id,
            barcode_lido=data.barcode_lido,
            observacao=data.observacao,
            origem=data.origem,
            created_at=datetime.utcnow(),
        )
        db.add(mov)

        self._apply_stock_effects(db, produto, mov)

        if commit:
            db.commit()
            db.refresh(mov)
        else:
            db.flush()
            db.refresh(mov)

        return mov

    # =========================
    # CREATE BATCH
    # =========================
    def create_batch(
        self,
        db: Session,
        items: List[MovimentacaoCreate],
    ) -> list[Movimentacao]:
        if not items:
            raise ValueError("Lista vazia.")

        created: list[Movimentacao] = []

        try:
            for item in items:
                created.append(self.create_one(db, item, commit=False))

            db.commit()

            for mov in created:
                db.refresh(mov)

            return created

        except Exception:
            db.rollback()
            raise

    # =========================
    # ESTORNAR
    # =========================
    def estornar(self, db: Session, mov_id: int, usuario_id: int) -> Movimentacao:
        original = self.get(db, mov_id)

        produto = db.get(Produto, original.produto_id)
        if not produto:
            raise ValueError("Produto da movimentação não encontrado.")

        tipo_estorno = self._tipo_estorno(original.tipo)

        inv = Movimentacao(
            produto_id=original.produto_id,
            evento_id=original.evento_id,
            aluguel_id=original.aluguel_id,
            usuario_id=usuario_id,
            setor_consumo_id=original.setor_consumo_id,
            tipo=tipo_estorno,
            quantidade_informada=original.quantidade_informada,
            unidade_informada_id=original.unidade_informada_id,
            fator_para_base=original.fator_para_base,
            quantidade_base=original.quantidade_base,
            custo_unitario=original.custo_unitario,
            local_origem_id=original.local_destino_id,
            local_destino_id=original.local_origem_id,
            lote_id=original.lote_id,
            embalagem_id=original.embalagem_id,
            barcode_lido=original.barcode_lido,
            observacao=f"Estorno da movimentação #{original.id}",
            origem="estorno",
            created_at=datetime.utcnow(),
        )
        db.add(inv)

        self._apply_stock_effects_reverse(db, produto, original)

        db.commit()
        db.refresh(inv)
        return inv

    # =========================
    # HELPERS
    # =========================
    def _tipo_estorno(self, tipo_original: str) -> str:
        mapa = {
            "entrada": "saida",
            "saida": "entrada",
            "transferencia": "transferencia",
            "ajuste": "ajuste",
            "devolucao": "saida",
        }
        if tipo_original not in mapa:
            raise ValueError("Tipo original inválido para estorno.")
        return mapa[tipo_original]

    def _get_or_create_saldo(
        self,
        db: Session,
        produto_id: int,
        local_id: int,
    ) -> EstoqueSaldo:
        stmt = select(EstoqueSaldo).where(
            EstoqueSaldo.produto_id == produto_id,
            EstoqueSaldo.local_id == local_id,
        )
        saldo = db.execute(stmt).scalar_one_or_none()

        if saldo:
            return saldo

        saldo = EstoqueSaldo(
            produto_id=produto_id,
            local_id=local_id,
            quantidade_base=0,
        )
        db.add(saldo)
        db.flush()
        return saldo

    def _assert_saldo(
        self,
        db: Session,
        produto_id: int,
        local_id: int | None,
        qtd: float,
    ) -> None:
        if local_id is None:
            raise ValueError("Local obrigatório para validar saldo.")

        saldo = db.execute(
            select(EstoqueSaldo).where(
                EstoqueSaldo.produto_id == produto_id,
                EstoqueSaldo.local_id == local_id,
            )
        ).scalar_one_or_none()

        atual = float(saldo.quantidade_base) if saldo else 0.0
        if atual < float(qtd) - 1e-9:
            raise ValueError("Saldo insuficiente para esta movimentação.")

    def _apply_stock_effects(
        self,
        db: Session,
        produto: Produto,
        mov: Movimentacao,
    ) -> None:
        qtd = float(mov.quantidade_base)

        # ENTRADA / DEVOLUÇÃO → aumenta no destino
        if mov.tipo in {"entrada", "devolucao"}:
            if mov.local_destino_id is None:
                raise ValueError("Movimentação sem local_destino_id.")

            saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_destino_id)
            saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")

                if lote.local_id != mov.local_destino_id:
                    raise ValueError(
                        "Lote deve estar no mesmo local do destino na entrada/devolução."
                    )

                lote.quantidade_base_atual = float(lote.quantidade_base_atual) + qtd

        # SAÍDA → reduz na origem
        elif mov.tipo == "saida":
            if mov.local_origem_id is None:
                raise ValueError("Movimentação sem local_origem_id.")

            saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_origem_id)
            novo_saldo = float(saldo.quantidade_base) - qtd
            if novo_saldo < -1e-9:
                raise ValueError("Saldo ficaria negativo.")
            saldo.quantidade_base = novo_saldo

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")

                if lote.local_id != mov.local_origem_id:
                    raise ValueError("Lote deve estar no mesmo local de origem na saída.")

                if float(lote.quantidade_base_atual) < qtd - 1e-9:
                    raise ValueError("Saldo insuficiente no lote.")

                lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

        # TRANSFERÊNCIA → origem - / destino +
        elif mov.tipo == "transferencia":
            if mov.local_origem_id is None or mov.local_destino_id is None:
                raise ValueError("Transferência sem local de origem/destino.")

            saldo_origem = self._get_or_create_saldo(db, mov.produto_id, mov.local_origem_id)
            novo_origem = float(saldo_origem.quantidade_base) - qtd
            if novo_origem < -1e-9:
                raise ValueError("Saldo de origem ficaria negativo.")
            saldo_origem.quantidade_base = novo_origem

            saldo_destino = self._get_or_create_saldo(db, mov.produto_id, mov.local_destino_id)
            saldo_destino.quantidade_base = float(saldo_destino.quantidade_base) + qtd

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")

                if lote.local_id != mov.local_origem_id:
                    raise ValueError("Lote deve estar no local de origem para transferir.")

                if float(lote.quantidade_base_atual) < qtd - 1e-9:
                    raise ValueError("Saldo insuficiente no lote para transferência.")

                lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

                stmt = select(Lote).where(
                    Lote.produto_id == mov.produto_id,
                    Lote.local_id == mov.local_destino_id,
                    Lote.codigo_lote == lote.codigo_lote,
                )
                lote_destino = db.execute(stmt).scalar_one_or_none()

                if not lote_destino:
                    lote_destino = Lote(
                        produto_id=mov.produto_id,
                        local_id=mov.local_destino_id,
                        codigo_lote=lote.codigo_lote,
                        validade=lote.validade,
                        quantidade_base_atual=0,
                    )
                    db.add(lote_destino)
                    db.flush()

                lote_destino.quantidade_base_atual = (
                    float(lote_destino.quantidade_base_atual) + qtd
                )

        # AJUSTE → origem reduz / destino aumenta
        elif mov.tipo == "ajuste":
            if mov.local_origem_id is not None:
                saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_origem_id)
                novo_saldo = float(saldo.quantidade_base) - qtd
                if novo_saldo < -1e-9:
                    raise ValueError("Saldo de origem ficaria negativo.")
                saldo.quantidade_base = novo_saldo

            if mov.local_destino_id is not None:
                saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_destino_id)
                saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")

                if mov.local_origem_id is not None:
                    if lote.local_id != mov.local_origem_id:
                        raise ValueError("Lote deve estar no local de origem para ajuste de redução.")
                    if float(lote.quantidade_base_atual) < qtd - 1e-9:
                        raise ValueError("Saldo insuficiente no lote para ajuste.")
                    lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

                elif mov.local_destino_id is not None:
                    if lote.local_id != mov.local_destino_id:
                        raise ValueError("Lote deve estar no local de destino para ajuste de aumento.")
                    lote.quantidade_base_atual = float(lote.quantidade_base_atual) + qtd

    def _apply_stock_effects_reverse(
        self,
        db: Session,
        produto: Produto,
        original: Movimentacao,
    ) -> None:
        qtd = float(original.quantidade_base)

        # reverte entrada/devolução: destino -
        if original.tipo in {"entrada", "devolucao"}:
            if original.local_destino_id is None:
                raise ValueError("Movimentação original sem local_destino_id.")

            saldo = self._get_or_create_saldo(db, original.produto_id, original.local_destino_id)
            self._assert_saldo(db, original.produto_id, original.local_destino_id, qtd)
            saldo.quantidade_base = float(saldo.quantidade_base) - qtd

            if produto.controla_lote and original.lote_id:
                lote = db.get(Lote, original.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")
                if float(lote.quantidade_base_atual) < qtd - 1e-9:
                    raise ValueError("Saldo insuficiente no lote para estornar entrada/devolução.")
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

        # reverte saída: origem +
        elif original.tipo == "saida":
            if original.local_origem_id is None:
                raise ValueError("Movimentação original sem local_origem_id.")

            saldo = self._get_or_create_saldo(db, original.produto_id, original.local_origem_id)
            saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            if produto.controla_lote and original.lote_id:
                lote = db.get(Lote, original.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) + qtd

        # reverte transferência: destino - / origem +
        elif original.tipo == "transferencia":
            if original.local_origem_id is None or original.local_destino_id is None:
                raise ValueError("Movimentação original sem local de origem/destino.")

            saldo_destino = self._get_or_create_saldo(db, original.produto_id, original.local_destino_id)
            self._assert_saldo(db, original.produto_id, original.local_destino_id, qtd)
            saldo_destino.quantidade_base = float(saldo_destino.quantidade_base) - qtd

            saldo_origem = self._get_or_create_saldo(db, original.produto_id, original.local_origem_id)
            saldo_origem.quantidade_base = float(saldo_origem.quantidade_base) + qtd

        # reverte ajuste
        elif original.tipo == "ajuste":
            if original.local_origem_id is not None:
                saldo = self._get_or_create_saldo(db, original.produto_id, original.local_origem_id)
                saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            if original.local_destino_id is not None:
                saldo = self._get_or_create_saldo(db, original.produto_id, original.local_destino_id)
                self._assert_saldo(db, original.produto_id, original.local_destino_id, qtd)
                saldo.quantidade_base = float(saldo.quantidade_base) - qtd

            if produto.controla_lote and original.lote_id:
                lote = db.get(Lote, original.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")

                if original.local_origem_id is not None:
                    lote.quantidade_base_atual = float(lote.quantidade_base_atual) + qtd
                elif original.local_destino_id is not None:
                    if float(lote.quantidade_base_atual) < qtd - 1e-9:
                        raise ValueError("Saldo insuficiente no lote para estornar ajuste.")
                    lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd