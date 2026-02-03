from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.unidades import Unidade
from app.schemas.unidades import UnidadeCreate, UnidadeUpdate


class UnidadeService:
    def list(self, db: Session) -> list[Unidade]:
        stmt = select(Unidade).order_by(Unidade.sigla.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, unidade_id: int) -> Unidade:
        unidade = db.get(Unidade, unidade_id)
        if not unidade:
            raise ValueError("Unidade não encontrada.")
        return unidade

    def create(self, db: Session, data: UnidadeCreate) -> Unidade:
        # sigla única
        exists = db.execute(select(Unidade).where(Unidade.sigla == data.sigla)).scalar_one_or_none()
        if exists:
            raise ValueError("Já existe uma unidade com essa sigla.")

        unidade = Unidade(sigla=data.sigla.strip(), descricao=data.descricao.strip())
        db.add(unidade)
        db.commit()
        db.refresh(unidade)
        return unidade

    def update(self, db: Session, unidade_id: int, data: UnidadeUpdate) -> Unidade:
        unidade = self.get(db, unidade_id)

        if data.sigla is not None:
            sigla = data.sigla.strip()
            exists = db.execute(
                select(Unidade).where(Unidade.sigla == sigla, Unidade.id != unidade_id)
            ).scalar_one_or_none()
            if exists:
                raise ValueError("Já existe uma unidade com essa sigla.")
            unidade.sigla = sigla

        if data.descricao is not None:
            unidade.descricao = data.descricao.strip()

        db.commit()
        db.refresh(unidade)
        return unidade

    def delete(self, db: Session, unidade_id: int) -> None:
        unidade = self.get(db, unidade_id)
        db.delete(unidade)
        db.commit()
