from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.compras import Compra
from app.models.fornecedores import Fornecedor
from app.models.usuarios import Usuario
from app.models.nfe_documentos import NfeDocumento
from app.models.compras_itens import CompraItem

from app.schemas.compras import CompraCreate, CompraUpdate, CompraConfirmarRequest, CompraConfirmarResponse
from app.schemas.movimentacoes_crud import MovimentacaoCreate
from app.services.movimentacoes_service import MovimentacoesService
from app.models.locais import Local
from app.models.produtos import Produto


class ComprasService:
    def list(self, db: Session, *, fornecedor_id: int | None = None, status: str | None = None) -> list[Compra]:
        stmt = select(Compra)

        if fornecedor_id is not None:
            stmt = stmt.where(Compra.fornecedor_id == fornecedor_id)
        if status is not None:
            stmt = stmt.where(Compra.status == status)

        stmt = stmt.order_by(Compra.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, compra_id: int) -> Compra:
        obj = db.get(Compra, compra_id)
        if not obj:
            raise ValueError("Compra não encontrada.")
        return obj

    def create(self, db: Session, data: CompraCreate) -> Compra:
        if not db.get(Fornecedor, data.fornecedor_id):
            raise ValueError("Fornecedor inválido.")
        if not db.get(Usuario, data.usuario_id):
            raise ValueError("Usuário inválido.")
        if data.nfe_documento_id is not None and not db.get(NfeDocumento, data.nfe_documento_id):
            raise ValueError("NF-e documento inválido.")

        obj = Compra(
            fornecedor_id=data.fornecedor_id,
            usuario_id=data.usuario_id,
            nfe_documento_id=data.nfe_documento_id,
            numero_documento=(data.numero_documento.strip() if data.numero_documento else None),
            data_compra=data.data_compra,
            valor_total=data.valor_total,
            status=(data.status.strip() if data.status else "rascunho"),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, compra_id: int, data: CompraUpdate) -> Compra:
        obj = self.get(db, compra_id)

        if data.fornecedor_id is not None:
            if not db.get(Fornecedor, data.fornecedor_id):
                raise ValueError("Fornecedor inválido.")
            obj.fornecedor_id = data.fornecedor_id

        if data.usuario_id is not None:
            if not db.get(Usuario, data.usuario_id):
                raise ValueError("Usuário inválido.")
            obj.usuario_id = data.usuario_id

        if data.nfe_documento_id is not None or "nfe_documento_id" in data.model_fields_set:
            if data.nfe_documento_id is not None and not db.get(NfeDocumento, data.nfe_documento_id):
                raise ValueError("NF-e documento inválido.")
            obj.nfe_documento_id = data.nfe_documento_id

        if data.numero_documento is not None or "numero_documento" in data.model_fields_set:
            obj.numero_documento = data.numero_documento.strip() if data.numero_documento else None

        if data.data_compra is not None or "data_compra" in data.model_fields_set:
            obj.data_compra = data.data_compra

        if data.valor_total is not None or "valor_total" in data.model_fields_set:
            obj.valor_total = data.valor_total

        if data.status is not None:
            obj.status = data.status.strip()

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, compra_id: int) -> None:
        obj = self.get(db, compra_id)
        db.delete(obj)
        db.commit()

    def itens(self, db: Session, compra_id: int) -> list[CompraItem]:
        self.get(db, compra_id)
        stmt = select(CompraItem).where(CompraItem.compra_id == compra_id).order_by(CompraItem.id.asc())
        return list(db.execute(stmt).scalars().all())

    def confirmar(self, db: Session, compra_id: int, req: CompraConfirmarRequest) -> CompraConfirmarResponse:
        compra = self.get(db, compra_id)

        if compra.status == "confirmada":
            return CompraConfirmarResponse(compra_id=compra.id, status=compra.status, movimentacoes_criadas=0)

        if not db.get(Local, req.local_destino_id):
            raise ValueError("Local destino inválido.")

        itens = self.itens(db, compra_id)
        if not itens:
            raise ValueError("Compra sem itens. Adicione itens antes de confirmar.")

        mov_service = MovimentacoesService()
        criadas = 0

        for it in itens:
            produto = db.get(Produto, it.produto_id)
            if not produto:
                raise ValueError(f"Produto inválido no item #{it.id}.")

            # se controla lote, exige lote_id
            if produto.controla_lote and not it.lote_id:
                raise ValueError(f"Produto '{produto.nome_comercial}' controla lote. Informe lote_id no item #{it.id}.")

            qtd_base = float(it.quantidade_informada) * float(it.fator_para_base)

            payload = MovimentacaoCreate(
                produto_id=it.produto_id,
                usuario_id=compra.usuario_id,
                tipo="entrada",
                origem=req.origem or "compra",
                quantidade_informada=float(it.quantidade_informada),
                unidade_informada_id=it.unidade_informada_id,
                fator_para_base=float(it.fator_para_base),
                custo_unitario=it.valor_unitario_informado,
                local_destino_id=req.local_destino_id,
                lote_id=it.lote_id,
                embalagem_id=it.embalagem_id,
                barcode_lido=it.barcode_lido,
                observacao=req.observacao or f"Entrada ref. compra #{compra.id}",
            )

            # cria mov + atualiza saldo/lote
            mov_service.create(db, payload)
            criadas += 1

            # salva quantidade_base calculada (útil para relatórios)
            it.quantidade_base = qtd_base

        compra.status = "confirmada"
        db.commit()

        return CompraConfirmarResponse(compra_id=compra.id, status=compra.status, movimentacoes_criadas=criadas)
