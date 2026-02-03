from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.produtos import Produto
from app.models.unidades import Unidade
from app.models.produto_embalagens import ProdutoEmbalagem
from app.schemas.produto_embalagens import EmbalagemCreate, EmbalagemUpdate


class EmbalagemService:
    def list_by_produto(self, db: Session, produto_id: int) -> list[ProdutoEmbalagem]:
        produto = db.get(Produto, produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")

        stmt = (
            select(ProdutoEmbalagem)
            .where(ProdutoEmbalagem.produto_id == produto_id)
            .order_by(ProdutoEmbalagem.principal.desc(), ProdutoEmbalagem.nome.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, embalagem_id: int) -> ProdutoEmbalagem:
        emb = db.get(ProdutoEmbalagem, embalagem_id)
        if not emb:
            raise ValueError("Embalagem não encontrada.")
        return emb

    def create(self, db: Session, produto_id: int, data: EmbalagemCreate) -> ProdutoEmbalagem:
        produto = db.get(Produto, produto_id)
        if not produto:
            raise ValueError("Produto não encontrado.")

        if not db.get(Unidade, data.unidade_id):
            raise ValueError("Unidade inválida.")

        # não permitir duplicar nome no mesmo produto (há unique constraint, mas validamos antes)
        exists = db.execute(
            select(ProdutoEmbalagem).where(
                ProdutoEmbalagem.produto_id == produto_id,
                ProdutoEmbalagem.nome == data.nome.strip(),
            )
        ).scalar_one_or_none()
        if exists:
            raise ValueError("Já existe uma embalagem com esse nome para este produto.")

        emb = ProdutoEmbalagem(
            produto_id=produto_id,
            nome=data.nome.strip(),
            unidade_id=data.unidade_id,
            fator_para_base=float(data.fator_para_base),
            permite_fracionar=bool(data.permite_fracionar),
            principal=bool(data.principal),
        )
        db.add(emb)

        # se marcou como principal, desmarca as outras
        if emb.principal:
            db.flush()
            self._unset_outros_principais(db, produto_id=produto_id, keep_id=emb.id)

        db.commit()
        db.refresh(emb)
        return emb

    def update(self, db: Session, embalagem_id: int, data: EmbalagemUpdate) -> ProdutoEmbalagem:
        emb = self.get(db, embalagem_id)

        if data.nome is not None:
            nome = data.nome.strip()
            exists = db.execute(
                select(ProdutoEmbalagem).where(
                    ProdutoEmbalagem.produto_id == emb.produto_id,
                    ProdutoEmbalagem.nome == nome,
                    ProdutoEmbalagem.id != embalagem_id,
                )
            ).scalar_one_or_none()
            if exists:
                raise ValueError("Já existe outra embalagem com esse nome para este produto.")
            emb.nome = nome

        if data.unidade_id is not None:
            if not db.get(Unidade, data.unidade_id):
                raise ValueError("Unidade inválida.")
            emb.unidade_id = data.unidade_id

        if data.fator_para_base is not None:
            emb.fator_para_base = float(data.fator_para_base)

        if data.permite_fracionar is not None:
            emb.permite_fracionar = bool(data.permite_fracionar)

        if data.principal is not None:
            emb.principal = bool(data.principal)
            if emb.principal:
                self._unset_outros_principais(db, produto_id=emb.produto_id, keep_id=emb.id)

        db.commit()
        db.refresh(emb)
        return emb

    def delete(self, db: Session, embalagem_id: int) -> None:
        emb = self.get(db, embalagem_id)
        db.delete(emb)
        db.commit()

    def definir_principal(self, db: Session, embalagem_id: int) -> ProdutoEmbalagem:
        emb = self.get(db, embalagem_id)
        emb.principal = True
        self._unset_outros_principais(db, produto_id=emb.produto_id, keep_id=emb.id)
        db.commit()
        db.refresh(emb)
        return emb

    def _unset_outros_principais(self, db: Session, *, produto_id: int, keep_id: int) -> None:
        stmt = select(ProdutoEmbalagem).where(
            ProdutoEmbalagem.produto_id == produto_id,
            ProdutoEmbalagem.id != keep_id,
            ProdutoEmbalagem.principal == True,  # noqa: E712
        )
        outros = list(db.execute(stmt).scalars().all())
        for o in outros:
            o.principal = False
