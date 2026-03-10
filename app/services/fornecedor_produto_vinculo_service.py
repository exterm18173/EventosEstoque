from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.fornecedor_produto_vinculo import FornecedorProdutoVinculo
from app.models.produtos import Produto
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.unidades import Unidade
from app.schemas.fornecedor_produto_vinculo import (
    FornecedorProdutoVinculoCreate,
    FornecedorProdutoVinculoUpdate,
)


class FornecedorProdutoVinculoService:
    def list(
        self,
        db: Session,
        *,
        fornecedor_cnpj: Optional[str] = None,
        produto_id: Optional[int] = None,
        termo: Optional[str] = None,
    ) -> list[FornecedorProdutoVinculo]:
        stmt = select(FornecedorProdutoVinculo)

        if fornecedor_cnpj:
            stmt = stmt.where(
                FornecedorProdutoVinculo.fornecedor_cnpj == self._only_digits(fornecedor_cnpj)
            )

        if produto_id is not None:
            stmt = stmt.where(FornecedorProdutoVinculo.produto_id == produto_id)

        if termo:
            termo_like = f"%{termo.strip()}%"
            stmt = stmt.where(
                or_(
                    FornecedorProdutoVinculo.codigo_fornecedor.ilike(termo_like),
                    FornecedorProdutoVinculo.descricao_fornecedor.ilike(termo_like),
                )
            )

        stmt = stmt.order_by(FornecedorProdutoVinculo.updated_at.desc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, vinculo_id: int) -> FornecedorProdutoVinculo:
        obj = db.get(FornecedorProdutoVinculo, vinculo_id)
        if not obj:
            raise ValueError("Vínculo fornecedor-produto não encontrado.")
        return obj

    def find_best_match(
        self,
        db: Session,
        *,
        fornecedor_cnpj: str,
        codigo_fornecedor: Optional[str],
        descricao_fornecedor: Optional[str],
    ) -> Optional[FornecedorProdutoVinculo]:
        fornecedor_cnpj = self._only_digits(fornecedor_cnpj)

        if codigo_fornecedor:
            obj = db.execute(
                select(FornecedorProdutoVinculo).where(
                    FornecedorProdutoVinculo.fornecedor_cnpj == fornecedor_cnpj,
                    FornecedorProdutoVinculo.codigo_fornecedor == codigo_fornecedor.strip(),
                )
            ).scalar_one_or_none()
            if obj:
                return obj

        if descricao_fornecedor:
            obj = db.execute(
                select(FornecedorProdutoVinculo).where(
                    FornecedorProdutoVinculo.fornecedor_cnpj == fornecedor_cnpj,
                    FornecedorProdutoVinculo.descricao_fornecedor == descricao_fornecedor.strip(),
                )
            ).scalar_one_or_none()
            if obj:
                return obj

        return None

    def create(self, db: Session, data: FornecedorProdutoVinculoCreate) -> FornecedorProdutoVinculo:
        self._validate_refs(
            db,
            produto_id=data.produto_id,
            embalagem_id=data.embalagem_id,
            unidade_informada_id=data.unidade_informada_id,
        )

        fornecedor_cnpj = self._only_digits(data.fornecedor_cnpj)

        existente = None
        if data.codigo_fornecedor:
            existente = db.execute(
                select(FornecedorProdutoVinculo).where(
                    FornecedorProdutoVinculo.fornecedor_cnpj == fornecedor_cnpj,
                    FornecedorProdutoVinculo.codigo_fornecedor == data.codigo_fornecedor.strip(),
                )
            ).scalar_one_or_none()

        if existente:
            raise ValueError("Já existe vínculo para este fornecedor e código do fornecedor.")

        obj = FornecedorProdutoVinculo(
            fornecedor_cnpj=fornecedor_cnpj,
            codigo_fornecedor=data.codigo_fornecedor.strip() if data.codigo_fornecedor else None,
            descricao_fornecedor=data.descricao_fornecedor.strip() if data.descricao_fornecedor else None,
            produto_id=data.produto_id,
            embalagem_id=data.embalagem_id,
            unidade_informada_id=data.unidade_informada_id,
            fator_para_base=data.fator_para_base,
            confianca=data.confianca,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, vinculo_id: int, data: FornecedorProdutoVinculoUpdate) -> FornecedorProdutoVinculo:
        obj = self.get(db, vinculo_id)

        if data.produto_id is not None or data.embalagem_id is not None or data.unidade_informada_id is not None:
            self._validate_refs(
                db,
                produto_id=data.produto_id or obj.produto_id,
                embalagem_id=data.embalagem_id if "embalagem_id" in data.model_fields_set else obj.embalagem_id,
                unidade_informada_id=(
                    data.unidade_informada_id if "unidade_informada_id" in data.model_fields_set else obj.unidade_informada_id
                ),
            )

        if data.fornecedor_cnpj is not None:
            obj.fornecedor_cnpj = self._only_digits(data.fornecedor_cnpj)

        if data.codigo_fornecedor is not None or "codigo_fornecedor" in data.model_fields_set:
            obj.codigo_fornecedor = data.codigo_fornecedor.strip() if data.codigo_fornecedor else None

        if data.descricao_fornecedor is not None or "descricao_fornecedor" in data.model_fields_set:
            obj.descricao_fornecedor = data.descricao_fornecedor.strip() if data.descricao_fornecedor else None

        if data.produto_id is not None:
            obj.produto_id = data.produto_id

        if data.embalagem_id is not None or "embalagem_id" in data.model_fields_set:
            obj.embalagem_id = data.embalagem_id

        if data.unidade_informada_id is not None or "unidade_informada_id" in data.model_fields_set:
            obj.unidade_informada_id = data.unidade_informada_id

        if data.fator_para_base is not None or "fator_para_base" in data.model_fields_set:
            obj.fator_para_base = data.fator_para_base

        if data.confianca is not None or "confianca" in data.model_fields_set:
            obj.confianca = data.confianca

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, vinculo_id: int) -> None:
        obj = self.get(db, vinculo_id)
        db.delete(obj)
        db.commit()

    def upsert_from_decision(
        self,
        db: Session,
        *,
        fornecedor_cnpj: str,
        codigo_fornecedor: Optional[str],
        descricao_fornecedor: Optional[str],
        produto_id: int,
        embalagem_id: Optional[int],
        unidade_informada_id: Optional[int],
        fator_para_base: Optional[float],
    ) -> FornecedorProdutoVinculo:
        fornecedor_cnpj = self._only_digits(fornecedor_cnpj)

        obj = self.find_best_match(
            db,
            fornecedor_cnpj=fornecedor_cnpj,
            codigo_fornecedor=codigo_fornecedor,
            descricao_fornecedor=descricao_fornecedor,
        )

        if obj:
            obj.produto_id = produto_id
            obj.embalagem_id = embalagem_id
            obj.unidade_informada_id = unidade_informada_id
            obj.fator_para_base = fator_para_base
            obj.confianca = 1.0
            db.commit()
            db.refresh(obj)
            return obj

        obj = FornecedorProdutoVinculo(
            fornecedor_cnpj=fornecedor_cnpj,
            codigo_fornecedor=codigo_fornecedor.strip() if codigo_fornecedor else None,
            descricao_fornecedor=descricao_fornecedor.strip() if descricao_fornecedor else None,
            produto_id=produto_id,
            embalagem_id=embalagem_id,
            unidade_informada_id=unidade_informada_id,
            fator_para_base=fator_para_base,
            confianca=1.0,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def _validate_refs(
        self,
        db: Session,
        *,
        produto_id: int,
        embalagem_id: Optional[int],
        unidade_informada_id: Optional[int],
    ) -> None:
        produto = db.get(Produto, produto_id)
        if not produto:
            raise ValueError("Produto inválido.")

        if embalagem_id is not None:
            emb = db.get(ProdutoEmbalagem, embalagem_id)
            if not emb or emb.produto_id != produto_id:
                raise ValueError("Embalagem inválida para este produto.")

        if unidade_informada_id is not None and not db.get(Unidade, unidade_informada_id):
            raise ValueError("Unidade informada inválida.")

    def _only_digits(self, value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())