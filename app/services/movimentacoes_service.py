from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from app.models.movimentacoes import Movimentacao
from app.models.produtos import Produto
from app.models.unidades import Unidade
from app.models.locais import Local
from app.models.lotes import Lote
from app.models.estoque_saldos import EstoqueSaldo

from app.schemas.movimentacoes_crud import MovimentacaoCreate


TIPOS_VALIDOS = {"entrada", "saida", "transferencia", "ajuste"}


class MovimentacoesService:
    def list(
        self,
        db: Session,
        *,
        produto_id: int | None = None,
        evento_id: int | None = None,
        aluguel_id: int | None = None,
        tipo: str | None = None,
        origem: str | None = None,
        local_id: int | None = None,
        data_inicio: str | None = None,  # YYYY-MM-DD (MVP)
        data_fim: str | None = None,     # YYYY-MM-DD (MVP)
    ) -> list[Movimentacao]:
        stmt = select(Movimentacao)

        if produto_id is not None:
            stmt = stmt.where(Movimentacao.produto_id == produto_id)
        if evento_id is not None:
            stmt = stmt.where(Movimentacao.evento_id == evento_id)
        if aluguel_id is not None:
            stmt = stmt.where(Movimentacao.aluguel_id == aluguel_id)
        if tipo is not None:
            stmt = stmt.where(Movimentacao.tipo == tipo)
        if origem is not None:
            stmt = stmt.where(Movimentacao.origem == origem)

        if local_id is not None:
            stmt = stmt.where(
                (Movimentacao.local_origem_id == local_id) | (Movimentacao.local_destino_id == local_id)
            )

        if data_inicio:
            stmt = stmt.where(Movimentacao.created_at >= f"{data_inicio}T00:00:00")
        if data_fim:
            stmt = stmt.where(Movimentacao.created_at <= f"{data_fim}T23:59:59")

        stmt = stmt.order_by(Movimentacao.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, mov_id: int) -> Movimentacao:
        m = db.get(Movimentacao, mov_id)
        if not m:
            raise ValueError("Movimentação não encontrada.")
        return m

    def create(self, db: Session, data: MovimentacaoCreate) -> Movimentacao:
        if data.tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use: {', '.join(sorted(TIPOS_VALIDOS))}.")

        produto = db.get(Produto, data.produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")
        if not db.get(Unidade, data.unidade_informada_id):
            raise ValueError("Unidade informada inválida.")

        # locais exigidos por tipo
        if data.tipo == "entrada":
            if data.local_destino_id is None:
                raise ValueError("Entrada exige local_destino_id.")
            if not db.get(Local, data.local_destino_id):
                raise ValueError("Local destino inválido.")

        elif data.tipo == "saida":
            if data.local_origem_id is None:
                raise ValueError("Saída exige local_origem_id.")
            if not db.get(Local, data.local_origem_id):
                raise ValueError("Local origem inválido.")

        elif data.tipo == "transferencia":
            if data.local_origem_id is None or data.local_destino_id is None:
                raise ValueError("Transferência exige local_origem_id e local_destino_id.")
            if data.local_origem_id == data.local_destino_id:
                raise ValueError("Transferência exige locais diferentes.")
            if not db.get(Local, data.local_origem_id) or not db.get(Local, data.local_destino_id):
                raise ValueError("Local origem/destino inválido.")

        elif data.tipo == "ajuste":
            # ajuste pode usar origem (negativo) ou destino (positivo), mas precisa de pelo menos 1
            if data.local_origem_id is None and data.local_destino_id is None:
                raise ValueError("Ajuste exige local_origem_id (redução) ou local_destino_id (aumento).")
            if data.local_origem_id is not None and not db.get(Local, data.local_origem_id):
                raise ValueError("Local origem inválido.")
            if data.local_destino_id is not None and not db.get(Local, data.local_destino_id):
                raise ValueError("Local destino inválido.")

        # lote: se controla lote, exige lote nas operações que mexem em saldo
        if produto.controla_lote:
            if data.tipo in {"entrada", "saida", "transferencia"} and data.lote_id is None:
                raise ValueError("Produto controla lote: informe lote_id.")
            if data.lote_id is not None:
                lote = db.get(Lote, data.lote_id)
                if not lote:
                    raise ValueError("Lote inválido.")
                if lote.produto_id != produto.id:
                    raise ValueError("Lote não pertence a este produto.")

        # calcular base
        quantidade_base = float(data.quantidade_informada) * float(data.fator_para_base)

        # valida saldo suficiente em saída/transferência/ajuste redução
        if data.tipo == "saida":
            self._assert_saldo(db, produto.id, data.local_origem_id, quantidade_base)
        elif data.tipo == "transferencia":
            self._assert_saldo(db, produto.id, data.local_origem_id, quantidade_base)
        elif data.tipo == "ajuste" and data.local_origem_id is not None:
            self._assert_saldo(db, produto.id, data.local_origem_id, quantidade_base)

        # cria movimentação
        mov = Movimentacao(
            produto_id=data.produto_id,
            evento_id=data.evento_id,
            aluguel_id=data.aluguel_id,
            usuario_id=data.usuario_id,
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

        # aplica efeitos no saldo/lote
        self._apply_stock_effects(db, produto, mov)

        db.commit()
        db.refresh(mov)
        return mov

    def estornar(self, db: Session, mov_id: int, usuario_id: int) -> Movimentacao:
        original = self.get(db, mov_id)
        produto = db.get(Produto, original.produto_id)
        if not produto:
            raise ValueError("Produto da movimentação não encontrado.")

        # cria uma movimentação inversa
        inv = Movimentacao(
            produto_id=original.produto_id,
            evento_id=original.evento_id,
            aluguel_id=original.aluguel_id,
            usuario_id=usuario_id,
            tipo=f"estorno_{original.tipo}",
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

        # reverte efeito
        self._apply_stock_effects_reverse(db, produto, original)

        db.commit()
        db.refresh(inv)
        return inv

    # ---------------- Helpers ----------------
    def _get_or_create_saldo(self, db: Session, produto_id: int, local_id: int) -> EstoqueSaldo:
        stmt = select(EstoqueSaldo).where(
            EstoqueSaldo.produto_id == produto_id,
            EstoqueSaldo.local_id == local_id,
        )
        saldo = db.execute(stmt).scalar_one_or_none()
        if saldo:
            return saldo
        saldo = EstoqueSaldo(produto_id=produto_id, local_id=local_id, quantidade_base=0)
        db.add(saldo)
        db.flush()
        return saldo

    def _assert_saldo(self, db: Session, produto_id: int, local_id: int | None, qtd: float) -> None:
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

    def _apply_stock_effects(self, db: Session, produto: Produto, mov: Movimentacao) -> None:
        qtd = float(mov.quantidade_base)

        if mov.tipo == "entrada":
            saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_destino_id)
            saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                # lote deve estar no mesmo local destino
                if lote.local_id != mov.local_destino_id:
                    raise ValueError("Lote deve estar no mesmo local do destino na entrada.")
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) + qtd

        elif mov.tipo == "saida":
            saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_origem_id)
            saldo.quantidade_base = float(saldo.quantidade_base) - qtd

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                if lote.local_id != mov.local_origem_id:
                    raise ValueError("Lote deve estar no mesmo local de origem na saída.")
                if float(lote.quantidade_base_atual) < qtd - 1e-9:
                    raise ValueError("Saldo insuficiente no lote.")
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

        elif mov.tipo == "transferencia":
            # origem -
            saldo_o = self._get_or_create_saldo(db, mov.produto_id, mov.local_origem_id)
            saldo_o.quantidade_base = float(saldo_o.quantidade_base) - qtd

            # destino +
            saldo_d = self._get_or_create_saldo(db, mov.produto_id, mov.local_destino_id)
            saldo_d.quantidade_base = float(saldo_d.quantidade_base) + qtd

            if produto.controla_lote and mov.lote_id:
                lote = db.get(Lote, mov.lote_id)
                if lote.local_id != mov.local_origem_id:
                    raise ValueError("Lote deve estar no local de origem para transferir.")
                if float(lote.quantidade_base_atual) < qtd - 1e-9:
                    raise ValueError("Saldo insuficiente no lote para transferência.")
                # move lote para o destino (modelo simples do MVP)
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

                # cria/usa um lote “espelho” no destino com mesmo codigo/validade
                stmt = select(Lote).where(
                    Lote.produto_id == mov.produto_id,
                    Lote.local_id == mov.local_destino_id,
                    Lote.codigo_lote == lote.codigo_lote,
                )
                lote_dest = db.execute(stmt).scalar_one_or_none()
                if not lote_dest:
                    lote_dest = Lote(
                        produto_id=mov.produto_id,
                        local_id=mov.local_destino_id,
                        codigo_lote=lote.codigo_lote,
                        validade=lote.validade,
                        quantidade_base_atual=0,
                    )
                    db.add(lote_dest)
                    db.flush()
                lote_dest.quantidade_base_atual = float(lote_dest.quantidade_base_atual) + qtd

        elif mov.tipo == "ajuste":
            # se tiver origem => reduz
            if mov.local_origem_id is not None:
                saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_origem_id)
                saldo.quantidade_base = float(saldo.quantidade_base) - qtd

            # se tiver destino => aumenta
            if mov.local_destino_id is not None:
                saldo = self._get_or_create_saldo(db, mov.produto_id, mov.local_destino_id)
                saldo.quantidade_base = float(saldo.quantidade_base) + qtd

    def _apply_stock_effects_reverse(self, db: Session, produto: Produto, original: Movimentacao) -> None:
        # reverte saldo/lote com base no original
        qtd = float(original.quantidade_base)

        if original.tipo == "entrada":
            saldo = self._get_or_create_saldo(db, original.produto_id, original.local_destino_id)
            self._assert_saldo(db, original.produto_id, original.local_destino_id, qtd)
            saldo.quantidade_base = float(saldo.quantidade_base) - qtd

            if produto.controla_lote and original.lote_id:
                lote = db.get(Lote, original.lote_id)
                if float(lote.quantidade_base_atual) < qtd - 1e-9:
                    raise ValueError("Saldo insuficiente no lote para estornar entrada.")
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) - qtd

        elif original.tipo == "saida":
            saldo = self._get_or_create_saldo(db, original.produto_id, original.local_origem_id)
            saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            if produto.controla_lote and original.lote_id:
                lote = db.get(Lote, original.lote_id)
                lote.quantidade_base_atual = float(lote.quantidade_base_atual) + qtd

        elif original.tipo == "transferencia":
            # volta: destino -, origem +
            saldo_d = self._get_or_create_saldo(db, original.produto_id, original.local_destino_id)
            self._assert_saldo(db, original.produto_id, original.local_destino_id, qtd)
            saldo_d.quantidade_base = float(saldo_d.quantidade_base) - qtd

            saldo_o = self._get_or_create_saldo(db, original.produto_id, original.local_origem_id)
            saldo_o.quantidade_base = float(saldo_o.quantidade_base) + qtd

        elif original.tipo == "ajuste":
            # se reduziu em origem => volta aumentando
            if original.local_origem_id is not None:
                saldo = self._get_or_create_saldo(db, original.produto_id, original.local_origem_id)
                saldo.quantidade_base = float(saldo.quantidade_base) + qtd

            # se aumentou em destino => volta reduzindo
            if original.local_destino_id is not None:
                saldo = self._get_or_create_saldo(db, original.produto_id, original.local_destino_id)
                self._assert_saldo(db, original.produto_id, original.local_destino_id, qtd)
                saldo.quantidade_base = float(saldo.quantidade_base) - qtd
