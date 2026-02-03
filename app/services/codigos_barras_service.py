from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.produtos import Produto
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.produto_codigos_barras import ProdutoCodigoBarras
from app.schemas.codigos_barras import CodigoBarrasCreate, CodigoBarrasUpdate, BarcodeLookupResponse


class CodigoBarrasService:
    def list_by_produto(self, db: Session, produto_id: int) -> list[ProdutoCodigoBarras]:
        if not db.get(Produto, produto_id):
            raise ValueError("Produto não encontrado.")

        stmt = (
            select(ProdutoCodigoBarras)
            .where(ProdutoCodigoBarras.produto_id == produto_id)
            .order_by(ProdutoCodigoBarras.principal.desc(), ProdutoCodigoBarras.codigo.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, barcode_id: int) -> ProdutoCodigoBarras:
        obj = db.get(ProdutoCodigoBarras, barcode_id)
        if not obj:
            raise ValueError("Código de barras não encontrado.")
        return obj

    def create(self, db: Session, produto_id: int, data: CodigoBarrasCreate) -> ProdutoCodigoBarras:
        produto = db.get(Produto, produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")

        emb = db.get(ProdutoEmbalagem, data.embalagem_id)
        if not emb:
            raise ValueError("Embalagem inválida.")
        if emb.produto_id != produto_id:
            raise ValueError("A embalagem informada não pertence a este produto.")

        codigo = data.codigo.strip()

        # código único (há constraint, mas validamos antes)
        exists = db.execute(
            select(ProdutoCodigoBarras).where(ProdutoCodigoBarras.codigo == codigo)
        ).scalar_one_or_none()
        if exists:
            raise ValueError("Este código de barras já está cadastrado.")

        obj = ProdutoCodigoBarras(
            produto_id=produto_id,
            embalagem_id=data.embalagem_id,
            codigo=codigo,
            tipo=data.tipo.strip(),
            principal=bool(data.principal),
            ativo=bool(data.ativo),
        )
        db.add(obj)

        if obj.principal:
            db.flush()
            self._unset_outros_principais(db, produto_id=produto_id, keep_id=obj.id)

        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, barcode_id: int, data: CodigoBarrasUpdate) -> ProdutoCodigoBarras:
        obj = self.get(db, barcode_id)

        if data.embalagem_id is not None:
            emb = db.get(ProdutoEmbalagem, data.embalagem_id)
            if not emb:
                raise ValueError("Embalagem inválida.")
            if emb.produto_id != obj.produto_id:
                raise ValueError("A embalagem informada não pertence ao mesmo produto deste código.")
            obj.embalagem_id = data.embalagem_id

        if data.codigo is not None:
            codigo = data.codigo.strip()
            exists = db.execute(
                select(ProdutoCodigoBarras).where(
                    ProdutoCodigoBarras.codigo == codigo,
                    ProdutoCodigoBarras.id != barcode_id,
                )
            ).scalar_one_or_none()
            if exists:
                raise ValueError("Este código de barras já está cadastrado.")
            obj.codigo = codigo

        if data.tipo is not None:
            obj.tipo = data.tipo.strip()

        if data.ativo is not None:
            obj.ativo = bool(data.ativo)

        if data.principal is not None:
            obj.principal = bool(data.principal)
            if obj.principal:
                self._unset_outros_principais(db, produto_id=obj.produto_id, keep_id=obj.id)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, barcode_id: int) -> None:
        obj = self.get(db, barcode_id)
        db.delete(obj)
        db.commit()

    def definir_principal(self, db: Session, barcode_id: int) -> ProdutoCodigoBarras:
        obj = self.get(db, barcode_id)
        obj.principal = True
        self._unset_outros_principais(db, produto_id=obj.produto_id, keep_id=obj.id)
        db.commit()
        db.refresh(obj)
        return obj

    def lookup(self, db: Session, codigo: str) -> BarcodeLookupResponse:
        codigo = codigo.strip()
        obj = db.execute(
            select(ProdutoCodigoBarras).where(
                ProdutoCodigoBarras.codigo == codigo,
                ProdutoCodigoBarras.ativo == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if not obj:
            raise ValueError("Código de barras não encontrado ou inativo.")

        emb = db.get(ProdutoEmbalagem, obj.embalagem_id)
        prod = db.get(Produto, obj.produto_id)
        if not emb or not prod:
            raise ValueError("Cadastro inconsistente para este código.")

        return BarcodeLookupResponse(
            codigo=obj.codigo,
            produto_id=prod.id,
            embalagem_id=emb.id,
            fator_para_base=float(emb.fator_para_base),
            unidade_base_id=prod.unidade_base_id,
            nome_produto=prod.nome_comercial,
            nome_embalagem=emb.nome,
            ativo=bool(obj.ativo),
            principal=bool(obj.principal),
        )

    def _unset_outros_principais(self, db: Session, *, produto_id: int, keep_id: int) -> None:
        stmt = select(ProdutoCodigoBarras).where(
            ProdutoCodigoBarras.produto_id == produto_id,
            ProdutoCodigoBarras.id != keep_id,
            ProdutoCodigoBarras.principal == True,  # noqa: E712
        )
        outros = list(db.execute(stmt).scalars().all())
        for o in outros:
            o.principal = False
