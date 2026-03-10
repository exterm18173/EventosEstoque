import re

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.setores_consumo import SetorConsumo
from app.schemas.setores_consumo import SetorConsumoCreate


class SetoresConsumoService:
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        nome = nome.strip()
        nome = re.sub(r"\s+", " ", nome)
        return nome

    def list(self, db: Session) -> list[SetorConsumo]:
        stmt = select(SetorConsumo).order_by(
            SetorConsumo.ativo.desc(),
            SetorConsumo.nome.asc(),
        )
        return db.execute(stmt).scalars().all()

    def get(self, db: Session, setor_id: int) -> SetorConsumo:
        setor = db.get(SetorConsumo, setor_id)
        if not setor:
            raise ValueError("Setor de consumo não encontrado.")
        return setor

    def create(self, db: Session, data: SetorConsumoCreate) -> SetorConsumo:
        nome_normalizado = self._normalizar_nome(data.nome)

        if not nome_normalizado:
            raise ValueError("Nome do setor de consumo é obrigatório.")

        existente = db.execute(
            select(SetorConsumo).where(
                func.lower(SetorConsumo.nome) == nome_normalizado.lower()
            )
        ).scalar_one_or_none()

        if existente:
            raise ValueError("Já existe um setor de consumo com esse nome.")

        setor = SetorConsumo(
            nome=nome_normalizado,
            ativo=data.ativo,
        )

        try:
            db.add(setor)
            db.commit()
            db.refresh(setor)
            return setor

        except IntegrityError:
            db.rollback()
            raise ValueError("Já existe um setor de consumo com esse nome.")

        except SQLAlchemyError:
            db.rollback()
            raise ValueError("Erro ao salvar o setor de consumo.")