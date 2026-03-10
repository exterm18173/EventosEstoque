from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.produtos import Produto
from app.models.produtos_base import ProdutoBase
from app.models.marcas import Marca
from app.models.unidades import Unidade
from app.models.estoque_saldos import EstoqueSaldo
from app.models.movimentacoes import Movimentacao
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.produto_codigos_barras import ProdutoCodigoBarras

from app.schemas.produtos import ProdutoCreate, ProdutoUpdate

import os, uuid, mimetypes
from fastapi import UploadFile

STORAGE_DIR = os.path.join("storage", "produtos")
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


class ProdutoService:
    def list(
        self,
        db: Session,
        *,
        produto_base_id: int | None = None,
        marca_id: int | None = None,
        ativo: bool | None = None,
        eh_alugavel: bool | None = None,
        q: str | None = None,
    ) -> list[Produto]:
        stmt = select(Produto)

        if produto_base_id is not None:
            stmt = stmt.where(Produto.produto_base_id == produto_base_id)

        if marca_id is not None:
            stmt = stmt.where(Produto.marca_id == marca_id)

        if ativo is not None:
            stmt = stmt.where(Produto.ativo == ativo)

        if eh_alugavel is not None:
            stmt = stmt.where(Produto.eh_alugavel == eh_alugavel)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Produto.nome_comercial.ilike(like))

        stmt = stmt.order_by(Produto.nome_comercial.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, produto_id: int) -> Produto:
        p = db.get(Produto, produto_id)
        if not p:
            raise ValueError("Produto não encontrado.")
        return p

    def create(self, db: Session, data: ProdutoCreate) -> Produto:
        # valida FK
        if not db.get(ProdutoBase, data.produto_base_id):
            raise ValueError("Produto base inválido.")
        if data.marca_id is not None and not db.get(Marca, data.marca_id):
            raise ValueError("Marca inválida.")
        if not db.get(Unidade, data.unidade_base_id):
            raise ValueError("Unidade base inválida.")

        p = Produto(
            produto_base_id=data.produto_base_id,
            marca_id=data.marca_id,
            nome_comercial=data.nome_comercial.strip(),
            unidade_base_id=data.unidade_base_id,
            sku=(data.sku.strip() if data.sku else None),
            ativo=data.ativo,
            eh_alugavel=data.eh_alugavel,
            controla_lote=data.controla_lote,
            controla_validade=data.controla_validade,
            estoque_minimo=data.estoque_minimo,
            custo_medio=data.custo_medio,
            preco_reposicao=data.preco_reposicao,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    def update(self, db: Session, produto_id: int, data: ProdutoUpdate) -> Produto:
        p = self.get(db, produto_id)

        if data.produto_base_id is not None:
            if not db.get(ProdutoBase, data.produto_base_id):
                raise ValueError("Produto base inválido.")
            p.produto_base_id = data.produto_base_id

        if data.marca_id is not None:
            if data.marca_id is not None and not db.get(Marca, data.marca_id):
                raise ValueError("Marca inválida.")
            p.marca_id = data.marca_id

        if data.nome_comercial is not None:
            p.nome_comercial = data.nome_comercial.strip()

        if data.unidade_base_id is not None:
            if not db.get(Unidade, data.unidade_base_id):
                raise ValueError("Unidade base inválida.")
            p.unidade_base_id = data.unidade_base_id

        if data.sku is not None:
            p.sku = data.sku.strip() if data.sku else None

        if data.ativo is not None:
            p.ativo = data.ativo

        if data.eh_alugavel is not None:
            p.eh_alugavel = data.eh_alugavel

        if data.controla_lote is not None:
            p.controla_lote = data.controla_lote

        if data.controla_validade is not None:
            p.controla_validade = data.controla_validade

        if data.estoque_minimo is not None or "estoque_minimo" in data.model_fields_set:
            p.estoque_minimo = data.estoque_minimo

        if data.custo_medio is not None or "custo_medio" in data.model_fields_set:
            p.custo_medio = data.custo_medio

        if data.preco_reposicao is not None or "preco_reposicao" in data.model_fields_set:
            p.preco_reposicao = data.preco_reposicao

        db.commit()
        db.refresh(p)
        return p

    def delete(self, db: Session, produto_id: int) -> None:
        p = self.get(db, produto_id)
        db.delete(p)
        db.commit()

    # --------- Consultas relacionadas ---------
    def saldos(self, db: Session, produto_id: int) -> list[EstoqueSaldo]:
        self.get(db, produto_id)
        stmt = select(EstoqueSaldo).where(EstoqueSaldo.produto_id == produto_id).order_by(EstoqueSaldo.local_id.asc())
        return list(db.execute(stmt).scalars().all())

    def movimentacoes(
        self,
        db: Session,
        produto_id: int,
        *,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        tipo: str | None = None,
        origem: str | None = None,
    ) -> list[Movimentacao]:
        self.get(db, produto_id)
        stmt = select(Movimentacao).where(Movimentacao.produto_id == produto_id)

        # filtros simples por string (YYYY-MM-DD) usando cast date
        if data_inicio:
            stmt = stmt.where(Movimentacao.created_at >= f"{data_inicio}T00:00:00")
        if data_fim:
            stmt = stmt.where(Movimentacao.created_at <= f"{data_fim}T23:59:59")
        if tipo:
            stmt = stmt.where(Movimentacao.tipo == tipo)
        if origem:
            stmt = stmt.where(Movimentacao.origem == origem)

        stmt = stmt.order_by(Movimentacao.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def embalagens(self, db: Session, produto_id: int) -> list[ProdutoEmbalagem]:
        self.get(db, produto_id)
        stmt = select(ProdutoEmbalagem).where(ProdutoEmbalagem.produto_id == produto_id).order_by(ProdutoEmbalagem.principal.desc(), ProdutoEmbalagem.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def codigos_barras(self, db: Session, produto_id: int) -> list[ProdutoCodigoBarras]:
        self.get(db, produto_id)
        stmt = select(ProdutoCodigoBarras).where(ProdutoCodigoBarras.produto_id == produto_id).order_by(ProdutoCodigoBarras.principal.desc(), ProdutoCodigoBarras.codigo.asc())
        return list(db.execute(stmt).scalars().all())
    def upload_foto(self, db: Session, produto_id: int, file: UploadFile) -> Produto:
        p = self.get(db, produto_id)

        if not file.content_type or file.content_type not in ALLOWED_MIME:
            raise ValueError("Formato inválido. Use JPG/PNG/WEBP.")

        os.makedirs(STORAGE_DIR, exist_ok=True)

        ext = mimetypes.guess_extension(file.content_type) or ".jpg"
        filename = f"{produto_id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join(STORAGE_DIR, filename)

        with open(path, "wb") as f:
            f.write(file.file.read())

        # (opcional) apagar foto antiga
        if p.foto_path and os.path.exists(p.foto_path):
            try: os.remove(p.foto_path)
            except: pass

        p.foto_path = path
        p.foto_mime = file.content_type
        p.foto_nome_original = file.filename

        db.commit()
        db.refresh(p)
        return p

    def delete_foto(self, db: Session, produto_id: int) -> Produto:
        p = self.get(db, produto_id)
        if p.foto_path and os.path.exists(p.foto_path):
            try: os.remove(p.foto_path)
            except: pass
        p.foto_path = None
        p.foto_mime = None
        p.foto_nome_original = None
        db.commit()
        db.refresh(p)
        return p