from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    def list(self, db: Session, *, q: str | None = None) -> list[Usuario]:
        stmt = select(Usuario)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                (Usuario.nome.ilike(like)) | (Usuario.email.ilike(like))
            )
        stmt = stmt.order_by(Usuario.nome.asc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, usuario_id: int) -> Usuario:
        obj = db.get(Usuario, usuario_id)
        if not obj:
            raise ValueError("Usuário não encontrado.")
        return obj

    def create(self, db: Session, data: UsuarioCreate) -> Usuario:
        email = data.email.strip().lower()

        # evita erro feio de unique (retorna mensagem amigável)
        exists = db.execute(
            select(Usuario).where(Usuario.email == email)
        ).scalar_one_or_none()
        if exists:
            raise ValueError("Já existe um usuário com este e-mail.")

        obj = Usuario(
            nome=data.nome.strip(),
            email=email,
            perfil=(data.perfil.strip() if data.perfil else "admin"),
            ativo=bool(data.ativo),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, usuario_id: int, data: UsuarioUpdate) -> Usuario:
        obj = self.get(db, usuario_id)

        if data.nome is not None:
            obj.nome = data.nome.strip()

        if data.email is not None:
            email = data.email.strip().lower()
            # valida unique no update
            exists = db.execute(
                select(Usuario).where(Usuario.email == email, Usuario.id != usuario_id)
            ).scalar_one_or_none()
            if exists:
                raise ValueError("Já existe um usuário com este e-mail.")
            obj.email = email

        if data.perfil is not None:
            obj.perfil = data.perfil.strip()

        if data.ativo is not None:
            obj.ativo = bool(data.ativo)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, usuario_id: int) -> None:
        obj = self.get(db, usuario_id)

        # IMPORTANTE:
        # Como seu Usuario tem FK em movimentacoes/compras/nfe_documentos,
        # deletar pode dar FK violation. Para MVP, eu recomendo "desativar".
        # Se você quiser deletar mesmo, precisa configurar cascade no model
        # ou deletar os filhos antes.
        raise ValueError("Para manter integridade, use desativar (ativo=false) em vez de excluir.")
