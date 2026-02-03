from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.produto_codigos_barras import ProdutoCodigoBarras
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.produtos import Produto
from app.models.unidades import Unidade

from app.schemas.barcode import BarcodeLookupResponse


class BarcodeService:
    def lookup(self, db: Session, codigo: str) -> BarcodeLookupResponse:
        code = (codigo or "").strip()
        if not code:
            raise ValueError("Código de barras vazio.")

        cb = db.execute(
            select(ProdutoCodigoBarras).where(
                ProdutoCodigoBarras.codigo == code,
                ProdutoCodigoBarras.ativo == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if not cb:
            raise ValueError("Código de barras não encontrado.")

        produto = db.get(Produto, cb.produto_id)
        if not produto:
            raise ValueError("Produto do código de barras não encontrado.")

        unidade = db.get(Unidade, produto.unidade_base_id)
        if not unidade:
            raise ValueError("Unidade base do produto não encontrada.")

        embalagem_id = cb.embalagem_id
        embalagem_nome = None

        # regra:
        # - se código está ligado a uma embalagem: usa unidade da embalagem e fator da embalagem
        # - se não: usa unidade base e fator 1
        if embalagem_id:
            emb = db.get(ProdutoEmbalagem, embalagem_id)
            if not emb or emb.produto_id != produto.id:
                raise ValueError("Embalagem inválida para este produto.")

            uni_emb = db.get(Unidade, emb.unidade_id)
            if not uni_emb:
                raise ValueError("Unidade da embalagem não encontrada.")

            return BarcodeLookupResponse(
                codigo=code,
                produto_id=produto.id,
                produto_nome=produto.nome_comercial,
                embalagem_id=emb.id,
                embalagem_nome=emb.nome,
                unidade_informada_id=uni_emb.id,
                unidade_sigla=uni_emb.sigla,
                fator_para_base=float(emb.fator_para_base),
            )

        # sem embalagem -> unidade base
        return BarcodeLookupResponse(
            codigo=code,
            produto_id=produto.id,
            produto_nome=produto.nome_comercial,
            embalagem_id=None,
            embalagem_nome=None,
            unidade_informada_id=unidade.id,
            unidade_sigla=unidade.sigla,
            fator_para_base=1.0,
        )
