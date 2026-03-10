from __future__ import annotations

from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lotes import Lote
from app.models.nota_conciliacao_item import NotaConciliacaoItem
from app.models.nota_recebida import NotaRecebida
from app.models.nota_recebida_item import NotaRecebidaItem
from app.models.produto_codigos_barras import ProdutoCodigoBarras
from app.models.produtos import Produto
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.unidades import Unidade
from app.schemas.nota_conciliacao import (
    NotaItemCriarProdutoRequest,
    NotaItemIgnorarRequest,
    NotaItemVincularProdutoRequest,
)
from app.services.fornecedor_produto_vinculo_service import FornecedorProdutoVinculoService


class NotaConciliacaoService:
    def __init__(self) -> None:
        self.vinculo_service = FornecedorProdutoVinculoService()

    def auto_conciliar_nota(self, db: Session, nota_id: int) -> None:
        nota = db.get(NotaRecebida, nota_id)
        if not nota:
            raise ValueError("Nota recebida não encontrada.")

        itens = db.execute(
            select(NotaRecebidaItem).where(NotaRecebidaItem.nota_recebida_id == nota_id)
        ).scalars().all()

        for item in itens:
            self.auto_conciliar_item(db, item.id, commit=False)

        db.commit()

    def auto_conciliar_item(self, db: Session, item_id: int, *, commit: bool = True) -> NotaConciliacaoItem:
        item = self._get_item(db, item_id)
        nota = db.get(NotaRecebida, item.nota_recebida_id)
        if not nota:
            raise ValueError("Nota da conciliação não encontrada.")

        conciliacao = self._get_or_create_conciliacao(db, item.id)

        # 1. por código de barras
        if item.codigo_barras:
            barcode = db.execute(
                select(ProdutoCodigoBarras).where(
                    ProdutoCodigoBarras.codigo == item.codigo_barras,
                    ProdutoCodigoBarras.ativo.is_(True),
                )
            ).scalar_one_or_none()

            if barcode:
                conciliacao.acao = "vincular_existente"
                conciliacao.produto_id = barcode.produto_id
                conciliacao.embalagem_id = barcode.embalagem_id
                conciliacao.unidade_informada_id = self._resolve_unidade_by_embalagem_or_produto(
                    db, barcode.embalagem_id, barcode.produto_id
                )
                conciliacao.fator_para_base = self._resolve_fator_by_embalagem(db, barcode.embalagem_id)
                conciliacao.barcode_final = item.codigo_barras
                conciliacao.validado = False

                item.produto_id = barcode.produto_id
                item.embalagem_id = barcode.embalagem_id
                item.unidade_informada_id = conciliacao.unidade_informada_id
                item.status_conciliacao = "sugerido"

                if commit:
                    db.commit()
                    db.refresh(conciliacao)
                return conciliacao

        # 2. por vínculo fornecedor-produto
        if nota.fornecedor_cnpj:
            vinculo = self.vinculo_service.find_best_match(
                db,
                fornecedor_cnpj=nota.fornecedor_cnpj,
                codigo_fornecedor=item.codigo_fornecedor,
                descricao_fornecedor=item.descricao,
            )
            if vinculo:
                conciliacao.acao = "vincular_existente"
                conciliacao.produto_id = vinculo.produto_id
                conciliacao.embalagem_id = vinculo.embalagem_id
                conciliacao.unidade_informada_id = vinculo.unidade_informada_id
                conciliacao.fator_para_base = vinculo.fator_para_base or 1.0
                conciliacao.barcode_final = item.codigo_barras
                conciliacao.validado = False

                item.produto_id = vinculo.produto_id
                item.embalagem_id = vinculo.embalagem_id
                item.unidade_informada_id = vinculo.unidade_informada_id
                item.status_conciliacao = "sugerido"

                if commit:
                    db.commit()
                    db.refresh(conciliacao)
                return conciliacao

        # 3. por similaridade de descrição
        produto = self._find_similar_product(db, item.descricao)
        if produto:
            conciliacao.acao = "conflito"
            conciliacao.produto_id = produto.id
            conciliacao.nome_produto_sugerido = produto.nome_comercial
            conciliacao.validado = False

            item.status_conciliacao = "conflito"

            if commit:
                db.commit()
                db.refresh(conciliacao)
            return conciliacao

        # 4. novo produto
        conciliacao.acao = "criar_produto"
        conciliacao.criar_produto_novo = True
        conciliacao.nome_produto_sugerido = item.descricao
        conciliacao.barcode_final = item.codigo_barras
        conciliacao.validado = False

        item.status_conciliacao = "novo_produto"

        if commit:
            db.commit()
            db.refresh(conciliacao)
        return conciliacao

    def vincular_produto(
        self,
        db: Session,
        item_id: int,
        data: NotaItemVincularProdutoRequest,
    ) -> NotaConciliacaoItem:
        item = self._get_item(db, item_id)
        nota = db.get(NotaRecebida, item.nota_recebida_id)
        if not nota:
            raise ValueError("Nota recebida não encontrada.")

        produto = db.get(Produto, data.produto_id)
        if not produto:
            raise ValueError("Produto inválido.")

        if not db.get(Unidade, data.unidade_informada_id):
            raise ValueError("Unidade informada inválida.")

        if data.embalagem_id is not None:
            emb = db.get(ProdutoEmbalagem, data.embalagem_id)
            if not emb or emb.produto_id != data.produto_id:
                raise ValueError("Embalagem inválida para o produto informado.")

        if data.lote_id is not None:
            lote = db.get(Lote, data.lote_id)
            if not lote or lote.produto_id != data.produto_id:
                raise ValueError("Lote inválido para o produto informado.")

        conciliacao = self._get_or_create_conciliacao(db, item.id)
        conciliacao.acao = "vincular_existente"
        conciliacao.produto_id = data.produto_id
        conciliacao.embalagem_id = data.embalagem_id
        conciliacao.unidade_informada_id = data.unidade_informada_id
        conciliacao.fator_para_base = data.fator_para_base
        conciliacao.barcode_final = data.barcode_final
        conciliacao.lote_id = data.lote_id
        conciliacao.observacao = data.observacao
        conciliacao.validado = True
        conciliacao.criar_produto_novo = False
        conciliacao.nome_produto_sugerido = produto.nome_comercial

        item.produto_id = data.produto_id
        item.embalagem_id = data.embalagem_id
        item.unidade_informada_id = data.unidade_informada_id
        item.lote_id = data.lote_id
        item.status_conciliacao = "vinculado"
        item.observacao = data.observacao

        if nota.fornecedor_cnpj:
            self.vinculo_service.upsert_from_decision(
                db,
                fornecedor_cnpj=nota.fornecedor_cnpj,
                codigo_fornecedor=item.codigo_fornecedor,
                descricao_fornecedor=item.descricao,
                produto_id=data.produto_id,
                embalagem_id=data.embalagem_id,
                unidade_informada_id=data.unidade_informada_id,
                fator_para_base=data.fator_para_base,
            )

        db.commit()
        db.refresh(conciliacao)
        return conciliacao

    def criar_produto_e_vincular(
        self,
        db: Session,
        item_id: int,
        data: NotaItemCriarProdutoRequest,
    ) -> NotaConciliacaoItem:
        item = self._get_item(db, item_id)
        nota = db.get(NotaRecebida, item.nota_recebida_id)
        if not nota:
            raise ValueError("Nota recebida não encontrada.")

        from app.models.marcas import Marca
        from app.models.produtos_base import ProdutoBase

        if not db.get(ProdutoBase, data.produto_base_id):
            raise ValueError("Produto base inválido.")

        if data.marca_id is not None and not db.get(Marca, data.marca_id):
            raise ValueError("Marca inválida.")

        unidade = db.get(Unidade, data.unidade_base_id)
        if not unidade:
            raise ValueError("Unidade base inválida.")

        if not db.get(Unidade, data.unidade_informada_id):
            raise ValueError("Unidade informada inválida.")

        produto = Produto(
            produto_base_id=data.produto_base_id,
            marca_id=data.marca_id,
            nome_comercial=data.nome_comercial.strip(),
            unidade_base_id=data.unidade_base_id,
            sku=data.sku.strip() if data.sku else None,
            ativo=data.ativo,
            eh_alugavel=data.eh_alugavel,
            controla_lote=data.controla_lote,
            controla_validade=data.controla_validade,
            estoque_minimo=data.estoque_minimo,
            custo_medio=data.custo_medio if data.custo_medio is not None else item.valor_unitario,
            preco_reposicao=data.preco_reposicao if data.preco_reposicao is not None else item.valor_unitario,
        )
        db.add(produto)
        db.flush()

        if data.barcode_final:
            embalagem_id = data.embalagem_id
            if embalagem_id is not None:
                emb = db.get(ProdutoEmbalagem, embalagem_id)
                if not emb or emb.produto_id != produto.id:
                    embalagem_id = None

            if embalagem_id is None:
                emb = db.execute(
                    select(ProdutoEmbalagem).where(
                        ProdutoEmbalagem.produto_id == produto.id
                    )
                ).scalar_one_or_none()
                embalagem_id = emb.id if emb else None

            if embalagem_id is not None:
                barcode_existente = db.execute(
                    select(ProdutoCodigoBarras).where(
                        ProdutoCodigoBarras.codigo == data.barcode_final.strip()
                    )
                ).scalar_one_or_none()

                if not barcode_existente:
                    db.add(
                        ProdutoCodigoBarras(
                            produto_id=produto.id,
                            embalagem_id=embalagem_id,
                            codigo=data.barcode_final.strip(),
                            tipo="ean13",
                            principal=True,
                            ativo=True,
                        )
                    )

        conciliacao = self._get_or_create_conciliacao(db, item.id)
        conciliacao.acao = "criar_produto"
        conciliacao.produto_id = produto.id
        conciliacao.embalagem_id = data.embalagem_id
        conciliacao.unidade_informada_id = data.unidade_informada_id
        conciliacao.fator_para_base = data.fator_para_base
        conciliacao.barcode_final = data.barcode_final
        conciliacao.lote_id = data.lote_id
        conciliacao.criar_produto_novo = True
        conciliacao.nome_produto_sugerido = produto.nome_comercial
        conciliacao.observacao = data.observacao
        conciliacao.validado = True

        item.produto_id = produto.id
        item.embalagem_id = data.embalagem_id
        item.unidade_informada_id = data.unidade_informada_id
        item.lote_id = data.lote_id
        item.status_conciliacao = "vinculado"
        item.observacao = data.observacao

        if nota.fornecedor_cnpj:
            self.vinculo_service.upsert_from_decision(
                db,
                fornecedor_cnpj=nota.fornecedor_cnpj,
                codigo_fornecedor=item.codigo_fornecedor,
                descricao_fornecedor=item.descricao,
                produto_id=produto.id,
                embalagem_id=data.embalagem_id,
                unidade_informada_id=data.unidade_informada_id,
                fator_para_base=data.fator_para_base,
            )

        db.commit()
        db.refresh(conciliacao)
        return conciliacao

    def ignorar_item(
        self,
        db: Session,
        item_id: int,
        data: NotaItemIgnorarRequest,
    ) -> NotaConciliacaoItem:
        item = self._get_item(db, item_id)
        conciliacao = self._get_or_create_conciliacao(db, item.id)

        conciliacao.acao = "ignorar"
        conciliacao.validado = True
        conciliacao.observacao = data.observacao

        item.status_conciliacao = "ignorado"
        item.observacao = data.observacao

        db.commit()
        db.refresh(conciliacao)
        return conciliacao

    def resumo_nota(self, db: Session, nota_id: int) -> dict:
        itens = db.execute(
            select(NotaRecebidaItem).where(NotaRecebidaItem.nota_recebida_id == nota_id)
        ).scalars().all()

        total = len(itens)
        pendentes = 0
        vinculados = 0
        novos = 0
        ignorados = 0
        conflitos = 0

        for item in itens:
            status = item.status_conciliacao
            if status in {"nao_analisado", "sugerido"}:
                pendentes += 1
            elif status == "vinculado":
                vinculados += 1
            elif status == "novo_produto":
                novos += 1
            elif status == "ignorado":
                ignorados += 1
            elif status == "conflito":
                conflitos += 1

        return {
            "total_itens": total,
            "pendentes": pendentes,
            "vinculados": vinculados,
            "novos_produtos": novos,
            "ignorados": ignorados,
            "conflitos": conflitos,
        }

    def _get_item(self, db: Session, item_id: int) -> NotaRecebidaItem:
        item = db.get(NotaRecebidaItem, item_id)
        if not item:
            raise ValueError("Item da nota não encontrado.")
        return item

    def _get_or_create_conciliacao(self, db: Session, item_id: int) -> NotaConciliacaoItem:
        obj = db.execute(
            select(NotaConciliacaoItem).where(NotaConciliacaoItem.nota_recebida_item_id == item_id)
        ).scalar_one_or_none()

        if obj:
            return obj

        obj = NotaConciliacaoItem(nota_recebida_item_id=item_id)
        db.add(obj)
        db.flush()
        return obj

    def _resolve_fator_by_embalagem(self, db: Session, embalagem_id: Optional[int]) -> float:
        if embalagem_id is None:
            return 1.0
        emb = db.get(ProdutoEmbalagem, embalagem_id)
        if not emb:
            return 1.0

        fator = getattr(emb, "fator_para_base", None)
        return float(fator) if fator else 1.0

    def _resolve_unidade_by_embalagem_or_produto(
        self,
        db: Session,
        embalagem_id: Optional[int],
        produto_id: int,
    ) -> Optional[int]:
        if embalagem_id is not None:
            emb = db.get(ProdutoEmbalagem, embalagem_id)
            if emb:
                unidade_id = getattr(emb, "unidade_id", None) or getattr(emb, "unidade_informada_id", None)
                if unidade_id:
                    return unidade_id

        produto = db.get(Produto, produto_id)
        return produto.unidade_base_id if produto else None

    def _find_similar_product(self, db: Session, descricao: str) -> Optional[Produto]:
        produtos = db.execute(select(Produto).where(Produto.ativo.is_(True))).scalars().all()

        melhor = None
        melhor_score = 0.0
        base = self._normalize_text(descricao)

        for produto in produtos:
            score = SequenceMatcher(None, base, self._normalize_text(produto.nome_comercial)).ratio()
            if score > melhor_score:
                melhor_score = score
                melhor = produto

        if melhor_score >= 0.82:
            return melhor
        return None

    def _normalize_text(self, text: str) -> str:
        return " ".join((text or "").lower().strip().split())