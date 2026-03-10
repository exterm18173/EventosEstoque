from __future__ import annotations
from datetime import date

from sqlalchemy.orm import Session

from app.models.alugueis import Aluguel
from app.models.aluguel_itens import AluguelItem
from app.models.locais import Local
from app.models.produtos import Produto

from app.schemas.movimentacoes_crud import MovimentacaoCreate
from app.services.movimentacoes_service import MovimentacoesService
import os, uuid, mimetypes
from fastapi import UploadFile
from app.models.aluguel_devolucao_fotos import AluguelDevolucaoFoto

DEVOLUCAO_FOTOS_DIR = os.path.join("storage", "alugueis", "devolucoes")
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

class AluguelAcoesService:
    def saida(
        self,
        db: Session,
        aluguel_id: int,
        *,
        local_origem_id: int,
        usuario_id: int,
        origem: str,
        observacao: str | None,
    ) -> int:
        aluguel = db.get(Aluguel, aluguel_id)
        if not aluguel:
            raise ValueError("Aluguel não encontrado.")
        if not db.get(Local, local_origem_id):
            raise ValueError("Local origem inválido.")
        if aluguel.status in {"cancelado", "devolvido"}:
            raise ValueError("Aluguel não permite saída neste status.")

        itens = db.query(AluguelItem).filter(AluguelItem.aluguel_id == aluguel_id).all()
        if not itens:
            raise ValueError("Aluguel sem itens.")

        mov_service = MovimentacoesService()
        criadas = 0

        for it in itens:
            produto = db.get(Produto, it.produto_id)
            if not produto:
                raise ValueError(f"Produto inválido no item do aluguel (produto_id={it.produto_id}).")

            unidade_base_id = produto.unidade_base_id
            if not unidade_base_id:
                raise ValueError(f"Produto '{produto.nome_comercial}' sem unidade_base_id configurada.")

            payload = MovimentacaoCreate(
                produto_id=it.produto_id,
                usuario_id=usuario_id,
                tipo="saida",
                origem=origem or "aluguel",
                quantidade_informada=float(it.quantidade_base),
                unidade_informada_id=unidade_base_id,
                fator_para_base=1.0,
                custo_unitario=None,
                local_origem_id=local_origem_id,
                local_destino_id=None,
                lote_id=None,
                embalagem_id=None,
                barcode_lido=None,
                aluguel_id=aluguel_id,
                evento_id=aluguel.evento_id,
                observacao=observacao or f"Saída aluguel #{aluguel_id}",
            )

            mov_service.create(db, payload)
            criadas += 1
            it.status_item = "retirado"

        aluguel.status = "em_andamento"
        db.commit()
        return criadas

    def devolucao(
        self,
        db: Session,
        aluguel_id: int,
        *,
        local_destino_id: int,
        usuario_id: int,
        origem: str,
        observacao: str | None,
    ) -> int:
        aluguel = db.get(Aluguel, aluguel_id)
        if not aluguel:
            raise ValueError("Aluguel não encontrado.")
        if not db.get(Local, local_destino_id):
            raise ValueError("Local destino inválido.")
        if aluguel.status in {"cancelado"}:
            raise ValueError("Aluguel cancelado não permite devolução.")

        itens = db.query(AluguelItem).filter(AluguelItem.aluguel_id == aluguel_id).all()
        if not itens:
            raise ValueError("Aluguel sem itens.")

        mov_service = MovimentacoesService()
        criadas = 0

        for it in itens:
            produto = db.get(Produto, it.produto_id)
            if not produto:
                raise ValueError(f"Produto inválido no item do aluguel (produto_id={it.produto_id}).")

            unidade_base_id = produto.unidade_base_id
            if not unidade_base_id:
                raise ValueError(f"Produto '{produto.nome_comercial}' sem unidade_base_id configurada.")

            faltante = float(it.quantidade_base) - float(it.quantidade_devolvida_base or 0.0)
            if faltante <= 1e-9:
                it.status_item = "devolvido"
                continue

            payload = MovimentacaoCreate(
                produto_id=it.produto_id,
                usuario_id=usuario_id,
                tipo="entrada",
                origem=origem or "aluguel",
                quantidade_informada=faltante,
                unidade_informada_id=unidade_base_id,
                fator_para_base=1.0,
                custo_unitario=None,
                local_destino_id=local_destino_id,
                local_origem_id=None,
                lote_id=None,
                embalagem_id=None,
                barcode_lido=None,
                aluguel_id=aluguel_id,
                evento_id=aluguel.evento_id,
                observacao=observacao or f"Devolução aluguel #{aluguel_id}",
            )

            mov_service.create(db, payload)
            criadas += 1

            it.quantidade_devolvida_base = float(it.quantidade_base)
            it.status_item = "devolvido"

        aluguel.status = "devolvido"
        db.commit()
        return criadas
    
    def devolver_item_com_foto(
        self,
        db: Session,
        *,
        aluguel_id: int,
        item_id: int,
        local_destino_id: int,
        usuario_id: int,
        quantidade_devolver_base: float,
        lote_id: int | None,
        origem: str,
        observacao: str | None,
        foto: UploadFile,
    ) -> int:
        aluguel = db.get(Aluguel, aluguel_id)
        if not aluguel:
            raise ValueError("Aluguel não encontrado.")
        if aluguel.status == "cancelado":
            raise ValueError("Aluguel cancelado não permite devolução.")

        if not db.get(Local, local_destino_id):
            raise ValueError("Local destino inválido.")

        item = db.get(AluguelItem, item_id)
        if not item or item.aluguel_id != aluguel_id:
            raise ValueError("Item não encontrado para este aluguel.")

        if not foto or not foto.content_type or foto.content_type not in ALLOWED_MIME:
            raise ValueError("Foto obrigatória (JPG/PNG/WEBP).")

        produto = db.get(Produto, item.produto_id)
        if not produto:
            raise ValueError("Produto inválido.")

        # se controla lote, devolução exige lote_id (teu MovimentacoesService valida isso)
        if produto.controla_lote and not lote_id:
            raise ValueError("Produto controla lote: informe lote_id na devolução.")

        faltante = float(item.quantidade_base) - float(item.quantidade_devolvida_base or 0.0)
        if faltante <= 1e-9:
            raise ValueError("Este item já está totalmente devolvido.")

        qtd = float(quantidade_devolver_base)
        if qtd <= 0:
            raise ValueError("Quantidade inválida.")
        if qtd > faltante + 1e-9:
            raise ValueError("Quantidade para devolver maior que a faltante.")

        # cria movimentação com tipo DEVOLUCAO (conforme teu service)
        mov_service = MovimentacoesService()
        payload = MovimentacaoCreate(
            produto_id=item.produto_id,
            usuario_id=usuario_id,
            tipo="devolucao",  # <-- importantíssimo
            origem=origem or "aluguel",
            quantidade_informada=qtd,
            unidade_informada_id=produto.unidade_base_id,
            fator_para_base=1.0,
            custo_unitario=None,
            local_destino_id=local_destino_id,
            local_origem_id=None,
            lote_id=lote_id,
            embalagem_id=None,
            barcode_lido=None,
            aluguel_id=aluguel_id,
            evento_id=aluguel.evento_id,
            observacao=observacao or f"Devolução aluguel #{aluguel_id} item #{item_id}",
        )

        mov = mov_service.create(db, payload)  # retorna Movimentacao

        # salva foto em disco
        os.makedirs(DEVOLUCAO_FOTOS_DIR, exist_ok=True)
        ext = mimetypes.guess_extension(foto.content_type) or ".jpg"
        filename = f"{aluguel_id}_{item_id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join(DEVOLUCAO_FOTOS_DIR, filename)

        with open(path, "wb") as f:
            f.write(foto.file.read())

        db.add(
            AluguelDevolucaoFoto(
                aluguel_item_id=item_id,
                usuario_id=usuario_id,
                movimentacao_id=mov.id,
                path=path,
                mime=foto.content_type,
                nome_original=foto.filename,
            )
        )

        # atualiza item (parcial ou total)
        item.quantidade_devolvida_base = float(item.quantidade_devolvida_base or 0.0) + qtd

        faltante_depois = float(item.quantidade_base) - float(item.quantidade_devolvida_base or 0.0)
        if faltante_depois <= 1e-9:
            item.status_item = "devolvido"
        else:
            item.status_item = "parcial"

        # status do aluguel
        itens = db.query(AluguelItem).filter(AluguelItem.aluguel_id == aluguel_id).all()
        todos_ok = all((float(i.quantidade_base) - float(i.quantidade_devolvida_base or 0.0)) <= 1e-9 for i in itens)

        if todos_ok:
            aluguel.status = "devolvido"
            aluguel.data_devolucao_real = date.today()
        else:
            aluguel.status = "devolucao_parcial"

        db.commit()
        return 1