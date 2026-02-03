from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.locais import Local
from app.schemas.locais import LocalCreate, LocalUpdate


class LocalService:
    def list(self, db: Session, *, q: str | None = None, tipo: str | None = None) -> list[Local]:
        stmt = select(Local)

        if tipo:
            stmt = stmt.where(Local.tipo == tipo)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Local.nome.ilike(like))

        stmt = stmt.order_by(Local.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, local_id: int) -> Local:
        obj = db.get(Local, local_id)
        if not obj:
            raise ValueError("Local não encontrado.")
        return obj

    def create(self, db: Session, data: LocalCreate) -> Local:
        obj = Local(
            nome=data.nome.strip(),
            tipo=(data.tipo.strip() if data.tipo else None),
            descricao=(data.descricao.strip() if data.descricao else None),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, local_id: int, data: LocalUpdate) -> Local:
        obj = self.get(db, local_id)

        if data.nome is not None:
            obj.nome = data.nome.strip()
        if data.tipo is not None:
            obj.tipo = data.tipo.strip() if data.tipo else None
        if data.descricao is not None:
            obj.descricao = data.descricao.strip() if data.descricao else None

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, local_id: int) -> None:
        obj = self.get(db, local_id)
        db.delete(obj)
        db.commit()
