from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.marcas import Marca
from app.schemas.marcas import MarcaCreate, MarcaUpdate


class MarcaService:
    def list(self, db: Session, *, q: str | None = None) -> list[Marca]:
        stmt = select(Marca)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Marca.nome.ilike(like))
        stmt = stmt.order_by(Marca.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, marca_id: int) -> Marca:
        marca = db.get(Marca, marca_id)
        if not marca:
            raise ValueError("Marca não encontrada.")
        return marca

    def create(self, db: Session, data: MarcaCreate) -> Marca:
        nome = data.nome.strip()
        exists = db.execute(select(Marca).where(Marca.nome == nome)).scalar_one_or_none()
        if exists:
            raise ValueError("Já existe uma marca com esse nome.")

        marca = Marca(nome=nome)
        db.add(marca)
        db.commit()
        db.refresh(marca)
        return marca

    def update(self, db: Session, marca_id: int, data: MarcaUpdate) -> Marca:
        marca = self.get(db, marca_id)

        if data.nome is not None:
            nome = data.nome.strip()
            exists = db.execute(
                select(Marca).where(Marca.nome == nome, Marca.id != marca_id)
            ).scalar_one_or_none()
            if exists:
                raise ValueError("Já existe uma marca com esse nome.")
            marca.nome = nome

        db.commit()
        db.refresh(marca)
        return marca

    def delete(self, db: Session, marca_id: int) -> None:
        marca = self.get(db, marca_id)
        db.delete(marca)
        db.commit()
