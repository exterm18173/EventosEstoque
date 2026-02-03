from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.alugueis import Aluguel
from app.models.aluguel_itens import AluguelItem
from app.models.locais import Local
from app.models.produtos import Produto

from app.schemas.movimentacoes_crud import MovimentacaoCreate
from app.services.movimentacoes_service import MovimentacoesService


class AluguelAcoesService:
    def saida(
        self,
        db: Session,
        aluguel_id: int,
        *,
        local_origem_id: int,
        usuario_id: int,
        origem: str,
        observacao: str | None,
    ) -> int:
        aluguel = db.get(Aluguel, aluguel_id)
        if not aluguel:
            raise ValueError("Aluguel não encontrado.")
        if not db.get(Local, local_origem_id):
            raise ValueError("Local origem inválido.")
        if aluguel.status in {"cancelado", "devolvido"}:
            raise ValueError("Aluguel não permite saída neste status.")

        itens = db.query(AluguelItem).filter(AluguelItem.aluguel_id == aluguel_id).all()
        if not itens:
            raise ValueError("Aluguel sem itens.")

        mov_service = MovimentacoesService()
        criadas = 0

        for it in itens:
            produto = db.get(Produto, it.produto_id)
            if not produto:
                raise ValueError(f"Produto inválido no item do aluguel (produto_id={it.produto_id}).")

            unidade_base_id = produto.unidade_base_id
            if not unidade_base_id:
                raise ValueError(f"Produto '{produto.nome_comercial}' sem unidade_base_id configurada.")

            payload = MovimentacaoCreate(
                produto_id=it.produto_id,
                usuario_id=usuario_id,
                tipo="saida",
                origem=origem or "aluguel",
                quantidade_informada=float(it.quantidade_base),
                unidade_informada_id=unidade_base_id,
                fator_para_base=1.0,
                custo_unitario=None,
                local_origem_id=local_origem_id,
                local_destino_id=None,
                lote_id=None,
                embalagem_id=None,
                barcode_lido=None,
                aluguel_id=aluguel_id,
                evento_id=aluguel.evento_id,
                observacao=observacao or f"Saída aluguel #{aluguel_id}",
            )

            mov_service.create(db, payload)
            criadas += 1
            it.status_item = "retirado"

        aluguel.status = "em_andamento"
        db.commit()
        return criadas

    def devolucao(
        self,
        db: Session,
        aluguel_id: int,
        *,
        local_destino_id: int,
        usuario_id: int,
        origem: str,
        observacao: str | None,
    ) -> int:
        aluguel = db.get(Aluguel, aluguel_id)
        if not aluguel:
            raise ValueError("Aluguel não encontrado.")
        if not db.get(Local, local_destino_id):
            raise ValueError("Local destino inválido.")
        if aluguel.status in {"cancelado"}:
            raise ValueError("Aluguel cancelado não permite devolução.")

        itens = db.query(AluguelItem).filter(AluguelItem.aluguel_id == aluguel_id).all()
        if not itens:
            raise ValueError("Aluguel sem itens.")

        mov_service = MovimentacoesService()
        criadas = 0

        for it in itens:
            produto = db.get(Produto, it.produto_id)
            if not produto:
                raise ValueError(f"Produto inválido no item do aluguel (produto_id={it.produto_id}).")

            unidade_base_id = produto.unidade_base_id
            if not unidade_base_id:
                raise ValueError(f"Produto '{produto.nome_comercial}' sem unidade_base_id configurada.")

            faltante = float(it.quantidade_base) - float(it.quantidade_devolvida_base or 0.0)
            if faltante <= 1e-9:
                it.status_item = "devolvido"
                continue

            payload = MovimentacaoCreate(
                produto_id=it.produto_id,
                usuario_id=usuario_id,
                tipo="entrada",
                origem=origem or "aluguel",
                quantidade_informada=faltante,
                unidade_informada_id=unidade_base_id,
                fator_para_base=1.0,
                custo_unitario=None,
                local_destino_id=local_destino_id,
                local_origem_id=None,
                lote_id=None,
                embalagem_id=None,
                barcode_lido=None,
                aluguel_id=aluguel_id,
                evento_id=aluguel.evento_id,
                observacao=observacao or f"Devolução aluguel #{aluguel_id}",
            )

            mov_service.create(db, payload)
            criadas += 1

            it.quantidade_devolvida_base = float(it.quantidade_base)
            it.status_item = "devolvido"

        aluguel.status = "devolvido"
        db.commit()
        return criadas
