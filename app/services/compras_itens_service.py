from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.compras import Compra
from app.models.compras_itens import CompraItem
from app.models.produtos import Produto
from app.models.unidades import Unidade
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.lotes import Lote

from app.schemas.compras_itens import CompraItemCreate, CompraItemUpdate


class ComprasItensService:
    def get_item(self, db: Session, item_id: int) -> CompraItem:
        obj = db.get(CompraItem, item_id)
        if not obj:
            raise ValueError("Item da compra não encontrado.")
        return obj

    def create(self, db: Session, compra_id: int, data: CompraItemCreate) -> CompraItem:
        compra = db.get(Compra, compra_id)
        if not compra:
            raise ValueError("Compra não encontrada.")
        if compra.status == "confirmada":
            raise ValueError("Compra já confirmada. Não é possível adicionar itens.")

        produto = db.get(Produto, data.produto_id)
        if not produto:
            raise ValueError("Produto inválido.")
        if not db.get(Unidade, data.unidade_informada_id):
            raise ValueError("Unidade informada inválida.")

        if data.embalagem_id is not None:
            emb = db.get(ProdutoEmbalagem, data.embalagem_id)
            if not emb or emb.produto_id != data.produto_id:
                raise ValueError("Embalagem inválida para este produto.")

        if produto.controla_lote and data.lote_id is not None:
            lote = db.get(Lote, data.lote_id)
            if not lote or lote.produto_id != produto.id:
                raise ValueError("Lote inválido para este produto.")

        qtd_base = float(data.quantidade_informada) * float(data.fator_para_base)

        obj = CompraItem(
            compra_id=compra_id,
            produto_id=data.produto_id,
            embalagem_id=data.embalagem_id,
            unidade_informada_id=data.unidade_informada_id,
            quantidade_informada=float(data.quantidade_informada),
            fator_para_base=float(data.fator_para_base),
            quantidade_base=qtd_base,
            valor_unitario_informado=data.valor_unitario_informado,
            valor_total=data.valor_total,
            lote_id=data.lote_id,
            barcode_lido=data.barcode_lido,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, item_id: int, data: CompraItemUpdate) -> CompraItem:
        obj = self.get_item(db, item_id)
        compra = db.get(Compra, obj.compra_id)
        if compra and compra.status == "confirmada":
            raise ValueError("Compra já confirmada. Não é possível editar itens.")

        if data.produto_id is not None:
            produto = db.get(Produto, data.produto_id)
            if not produto:
                raise ValueError("Produto inválido.")
            obj.produto_id = data.produto_id

        if data.unidade_informada_id is not None:
            if not db.get(Unidade, data.unidade_informada_id):
                raise ValueError("Unidade informada inválida.")
            obj.unidade_informada_id = data.unidade_informada_id

        if data.embalagem_id is not None or "embalagem_id" in data.model_fields_set:
            if data.embalagem_id is not None:
                emb = db.get(ProdutoEmbalagem, data.embalagem_id)
                if not emb or emb.produto_id != obj.produto_id:
                    raise ValueError("Embalagem inválida para este produto.")
            obj.embalagem_id = data.embalagem_id

        if data.quantidade_informada is not None:
            obj.quantidade_informada = float(data.quantidade_informada)

        if data.fator_para_base is not None:
            obj.fator_para_base = float(data.fator_para_base)

        # recalcula base quando necessário
        if (
            ("quantidade_informada" in data.model_fields_set)
            or ("fator_para_base" in data.model_fields_set)
        ):
            obj.quantidade_base = float(obj.quantidade_informada) * float(obj.fator_para_base)

        if data.valor_unitario_informado is not None or "valor_unitario_informado" in data.model_fields_set:
            obj.valor_unitario_informado = data.valor_unitario_informado

        if data.valor_total is not None or "valor_total" in data.model_fields_set:
            obj.valor_total = data.valor_total

        if data.lote_id is not None or "lote_id" in data.model_fields_set:
            if data.lote_id is not None:
                lote = db.get(Lote, data.lote_id)
                if not lote or lote.produto_id != obj.produto_id:
                    raise ValueError("Lote inválido para este produto.")
            obj.lote_id = data.lote_id

        if data.barcode_lido is not None or "barcode_lido" in data.model_fields_set:
            obj.barcode_lido = data.barcode_lido

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, item_id: int) -> None:
        obj = self.get_item(db, item_id)
        compra = db.get(Compra, obj.compra_id)
        if compra and compra.status == "confirmada":
            raise ValueError("Compra já confirmada. Não é possível excluir itens.")
        db.delete(obj)
        db.commit()

    def list_by_compra(self, db: Session, compra_id: int) -> list[CompraItem]:
        if not db.get(Compra, compra_id):
            raise ValueError("Compra não encontrada.")
        stmt = select(CompraItem).where(CompraItem.compra_id == compra_id).order_by(CompraItem.id.asc())
        return list(db.execute(stmt).scalars().all())
