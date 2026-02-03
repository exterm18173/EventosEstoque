from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.categorias_produto import CategoriaProduto
from app.schemas.categorias_produto import (
    CategoriaProdutoCreate,
    CategoriaProdutoUpdate,
)


class CategoriaProdutoService:
    def list(
        self,
        db: Session,
        *,
        tipo: str | None = None,
        parent_id: int | None = None,
        q: str | None = None,
    ) -> list[CategoriaProduto]:
        stmt = select(CategoriaProduto)

        if tipo:
            stmt = stmt.where(CategoriaProduto.tipo == tipo)

        if parent_id is not None:
            stmt = stmt.where(CategoriaProduto.parent_id == parent_id)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(CategoriaProduto.nome.ilike(like))

        stmt = stmt.order_by(CategoriaProduto.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, categoria_id: int) -> CategoriaProduto:
        cat = db.get(CategoriaProduto, categoria_id)
        if not cat:
            raise ValueError("Categoria não encontrada.")
        return cat

    def create(self, db: Session, data: CategoriaProdutoCreate) -> CategoriaProduto:
        parent = None
        if data.parent_id is not None:
            parent = self.get(db, data.parent_id)  # valida parent
            # se quiser travar tipo herdado, dá pra forçar aqui (opcional)

        cat = CategoriaProduto(
            nome=data.nome.strip(),
            tipo=(data.tipo.strip() if data.tipo else None),
            parent_id=parent.id if parent else None,
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    def update(self, db: Session, categoria_id: int, data: CategoriaProdutoUpdate) -> CategoriaProduto:
        cat = self.get(db, categoria_id)

        if data.nome is not None:
            cat.nome = data.nome.strip()

        if data.tipo is not None:
            cat.tipo = data.tipo.strip() if data.tipo else None

        if data.parent_id is not None:
            if data.parent_id == categoria_id:
                raise ValueError("Uma categoria não pode ser pai dela mesma.")
            parent = self.get(db, data.parent_id)
            # evitar ciclos simples: não permitir setar pai como um descendente
            if self._is_descendant(db, possible_parent_id=data.parent_id, child_id=categoria_id):
                raise ValueError("Não é permitido criar ciclo na árvore de categorias.")
            cat.parent_id = parent.id

        if data.parent_id is None and "parent_id" in data.model_fields_set:
            # permite remover pai explicitamente
            cat.parent_id = None

        db.commit()
        db.refresh(cat)
        return cat

    def delete(self, db: Session, categoria_id: int) -> None:
        cat = self.get(db, categoria_id)

        # bloquear delete se tiver filhos (mais seguro)
        has_children = db.execute(
            select(CategoriaProduto.id).where(CategoriaProduto.parent_id == categoria_id)
        ).first()
        if has_children:
            raise ValueError("Não é possível excluir: a categoria possui subcategorias.")

        db.delete(cat)
        db.commit()

    def tree(self, db: Session, *, tipo: str | None = None) -> list[dict]:
        # pega tudo e monta árvore em memória
        stmt = select(CategoriaProduto).order_by(CategoriaProduto.nome.asc())
        if tipo:
            stmt = stmt.where(CategoriaProduto.tipo == tipo)

        cats = list(db.execute(stmt).scalars().all())

        by_id: dict[int, dict] = {}
        roots: list[dict] = []

        for c in cats:
            by_id[c.id] = {
                "id": c.id,
                "nome": c.nome,
                "tipo": c.tipo,
                "parent_id": c.parent_id,
                "children": [],
            }

        for c in cats:
            node = by_id[c.id]
            if c.parent_id and c.parent_id in by_id:
                by_id[c.parent_id]["children"].append(node)
            else:
                roots.append(node)

        return roots

    def _is_descendant(self, db: Session, *, possible_parent_id: int, child_id: int) -> bool:
        # checagem simples subindo pelos pais do possible_parent
        current = self.get(db, possible_parent_id)
        while current.parent_id is not None:
            if current.parent_id == child_id:
                return True
            current = db.get(CategoriaProduto, current.parent_id)
            if not current:
                break
        return False
