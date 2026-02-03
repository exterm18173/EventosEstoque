from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.clientes import Cliente
from app.schemas.clientes import ClienteCreate, ClienteUpdate


class ClienteService:
    def list(self, db: Session, *, q: str | None = None) -> list[Cliente]:
        stmt = select(Cliente)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Cliente.nome.ilike(like))
        stmt = stmt.order_by(Cliente.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, cliente_id: int) -> Cliente:
        obj = db.get(Cliente, cliente_id)
        if not obj:
            raise ValueError("Cliente não encontrado.")
        return obj

    def create(self, db: Session, data: ClienteCreate) -> Cliente:
        obj = Cliente(
            nome=data.nome.strip(),
            documento=(data.documento.strip() if data.documento else None),
            telefone=(data.telefone.strip() if data.telefone else None),
            email=(data.email.strip().lower() if data.email else None),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, cliente_id: int, data: ClienteUpdate) -> Cliente:
        obj = self.get(db, cliente_id)

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

    def delete(self, db: Session, cliente_id: int) -> None:
        obj = self.get(db, cliente_id)
        db.delete(obj)
        db.commit()
