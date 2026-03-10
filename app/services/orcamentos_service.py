from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.orcamento import Orcamento, OrcamentoItem
from app.schemas.orcamentos import OrcamentoCreate, OrcamentoUpdate
from app.schemas.orcamento_itens import OrcamentoItemCreate, OrcamentoItemUpdate

# para converter:
from app.models.alugueis import Aluguel  # ajuste se seu model chama diferente
from app.models.aluguel_itens import AluguelItem  # ajuste se seu model chama diferente
from typing import List


class OrcamentoService:
    # --------------------
    # ORCAMENTOS
    # --------------------
    def list(
        self,
        db: Session,
        q: str | None = None,
        status: str | None = None,
        cliente_id: int | None = None,
        evento_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Orcamento]:
        stmt = select(Orcamento)

        if status:
            stmt = stmt.where(Orcamento.status == status)

        if cliente_id:
            stmt = stmt.where(Orcamento.cliente_id == cliente_id)

        if evento_id:
            stmt = stmt.where(Orcamento.evento_id == evento_id)

        # busca simples: por id (se q for num) ou por status
        if q:
            qq = q.strip()
            if qq.isdigit():
                stmt = stmt.where(Orcamento.id == int(qq))
            else:
                stmt = stmt.where(Orcamento.status.ilike(f"%{qq}%"))

        stmt = stmt.order_by(Orcamento.id.desc()).offset(offset).limit(limit)
        return db.execute(stmt).scalars().all()

    def get(self, db: Session, orcamento_id: int) -> Orcamento:
        obj = db.get(Orcamento, orcamento_id)
        if not obj:
            raise ValueError("Orçamento não encontrado.")
        return obj

    def create(self, db: Session, payload: OrcamentoCreate) -> Orcamento:
        obj = Orcamento(**payload.model_dump(exclude_unset=True))
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, orcamento_id: int, payload: OrcamentoUpdate) -> Orcamento:
        obj = self.get(db, orcamento_id)
        data = payload.model_dump(exclude_unset=True)

        for k, v in data.items():
            setattr(obj, k, v)

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, orcamento_id: int) -> None:
        obj = self.get(db, orcamento_id)
        db.delete(obj)
        db.commit()

    # --------------------
    # ITENS
    # --------------------
    def list_itens(self, db: Session, orcamento_id: int) -> List[OrcamentoItem]:

        self.get(db, orcamento_id)  # valida existência
        stmt = (
            select(OrcamentoItem)
            .where(OrcamentoItem.orcamento_id == orcamento_id)
            .order_by(OrcamentoItem.id.desc())
        )
        return db.execute(stmt).scalars().all()

    def add_item(self, db: Session, orcamento_id: int, payload: OrcamentoItemCreate) -> OrcamentoItem:
        self.get(db, orcamento_id)

        it = OrcamentoItem(
            orcamento_id=orcamento_id,
            **payload.model_dump(exclude_unset=True),
        )
        db.add(it)
        db.commit()
        db.refresh(it)
        return it

    def update_item(
        self,
        db: Session,
        orcamento_id: int,
        item_id: int,
        payload: OrcamentoItemUpdate,
    ) -> OrcamentoItem:
        self.get(db, orcamento_id)

        it = db.get(OrcamentoItem, item_id)
        if not it or it.orcamento_id != orcamento_id:
            raise ValueError("Item do orçamento não encontrado.")

        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(it, k, v)

        db.commit()
        db.refresh(it)
        return it

    def delete_item(self, db: Session, orcamento_id: int, item_id: int) -> None:
        self.get(db, orcamento_id)

        it = db.get(OrcamentoItem, item_id)
        if not it or it.orcamento_id != orcamento_id:
            raise ValueError("Item do orçamento não encontrado.")

        db.delete(it)
        db.commit()

    # --------------------
    # CONVERTER PARA ALUGUEL
    # --------------------
    def to_aluguel(
        self,
        db: Session,
        orcamento_id: int,
        status_aluguel: str = "aberto",
        copiar_datas: bool = True,
        copiar_observacao: bool = True,
    ) -> Aluguel:
        orc = self.get(db, orcamento_id)

        if orc.status in ("convertido", "cancelado"):
            raise ValueError("Este orçamento não pode ser convertido.")

        itens = self.list_itens(db, orcamento_id)
        if not itens:
            raise ValueError("Não é possível converter: orçamento sem itens.")

        aluguel = Aluguel(
            cliente_id=orc.cliente_id,
            evento_id=orc.evento_id,
            status=status_aluguel,
            valor_total=orc.valor_total,
            observacao=(orc.observacao if copiar_observacao else None),
            data_saida_prevista=(orc.data_saida_prevista if copiar_datas else None),
            data_devolucao_prevista=(orc.data_devolucao_prevista if copiar_datas else None),
        )
        db.add(aluguel)
        db.flush()  # pega aluguel.id sem commit ainda

        for it in itens:
            db.add(
                AluguelItem(
                    aluguel_id=aluguel.id,
                    produto_id=it.produto_id,
                    quantidade_base=float(it.quantidade_base),
                    quantidade_devolvida_base=0,
                    valor_unitario=float(it.valor_unitario),
                    status_item="pendente",
                    observacao=it.observacao,
                )
            )

        # marca orçamento como convertido
        orc.status = "convertido"

        db.commit()
        db.refresh(aluguel)
        return aluguel
