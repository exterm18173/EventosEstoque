from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.fornecedores import Fornecedor
from app.schemas.fornecedores import FornecedorCreate, FornecedorUpdate


class FornecedorService:
    def list(self, db: Session, *, q: str | None = None) -> list[Fornecedor]:
        stmt = select(Fornecedor)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Fornecedor.nome.ilike(like))
        stmt = stmt.order_by(Fornecedor.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, fornecedor_id: int) -> Fornecedor:
        obj = db.get(Fornecedor, fornecedor_id)
        if not obj:
            raise ValueError("Fornecedor não encontrado.")
        return obj

    def create(self, db: Session, data: FornecedorCreate) -> Fornecedor:
        obj = Fornecedor(
            nome=data.nome.strip(),
            documento=(data.documento.strip() if data.documento else None),
            telefone=(data.telefone.strip() if data.telefone else None),
            email=(data.email.strip().lower() if data.email else None),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, fornecedor_id: int, data: FornecedorUpdate) -> Fornecedor:
        obj = self.get(db, fornecedor_id)

        if data.nome is not None:
            obj.nome = data.nome.strip()
        if data.documento is not None:
            obj.documento = data.documento.strip() if data.documento else None
        if data.telefone is not None:
            obj.telefone = data.telefone.strip() if data.telefone else None
        if data.email is not None:
            obj.email = data.email.strip().lower() if data.email else None

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, fornecedor_id: int) -> None:
        obj = self.get(db, fornecedor_id)
        db.delete(obj)
        db.commit()
