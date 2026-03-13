from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compras import Compra
from app.models.compras_itens import CompraItem
from app.models.nota_importacao_log import NotaImportacaoLog
from app.models.nota_recebida import NotaRecebida
from app.models.nota_recebida_item import NotaRecebidaItem
from app.schemas.compras import CompraConfirmarRequest
from app.schemas.nota_importacao import (
    NotaImportacaoConfirmarCompraResponse,
    NotaImportacaoGerarCompraResponse,
)
from app.services.compras_service import ComprasService
from app.services.nota_conciliacao_service import NotaConciliacaoService


class NotaImportacaoService:
    def __init__(self) -> None:
        self.compras_service = ComprasService()
        self.conciliacao_service = NotaConciliacaoService()

    def gerar_compra(
        self,
        db: Session,
        *,
        nota_id: int,
        usuario_id: int,
        fornecedor_id: int | None = None,
        observacao: str | None = None,
    ) -> NotaImportacaoGerarCompraResponse:
        nota = self._get_nota(db, nota_id)

        if nota.compra_id is not None:
            raise ValueError("Esta nota já possui compra gerada.")

        resumo = self.conciliacao_service.resumo_nota(db, nota_id)
        if resumo["pendentes"] > 0 or resumo["conflitos"] > 0:
            raise ValueError("Ainda existem itens pendentes ou em conflito.")

        final_fornecedor_id = fornecedor_id or nota.fornecedor_id
        if final_fornecedor_id is None:
            raise ValueError("Fornecedor não definido para esta nota.")

        compra = Compra(
            fornecedor_id=final_fornecedor_id,
            usuario_id=usuario_id,
            numero_documento=nota.numero,
            data_compra=(nota.data_emissao.date() if nota.data_emissao else date.today()),
            valor_total=nota.valor_total,
            status="rascunho",
        )
        db.add(compra)
        db.flush()

        itens = db.execute(
            select(NotaRecebidaItem).where(NotaRecebidaItem.nota_recebida_id == nota_id)
        ).scalars().all()

        criados = 0
        for item in itens:
            if item.status_conciliacao == "ignorado":
                continue

            if not item.produto_id or not item.unidade_informada_id:
                raise ValueError(f"Item #{item.numero_item} sem conciliação completa.")

            fator = self._resolve_fator(db, item.id)
            qtd_base = float(item.quantidade) * float(fator)

            db.add(
                CompraItem(
                    compra_id=compra.id,
                    produto_id=item.produto_id,
                    embalagem_id=item.embalagem_id,
                    unidade_informada_id=item.unidade_informada_id,
                    quantidade_informada=float(item.quantidade),
                    fator_para_base=float(fator),
                    quantidade_base=qtd_base,
                    valor_unitario_informado=item.valor_unitario,
                    valor_total=item.valor_total,
                    lote_id=item.lote_id,
                    barcode_lido=item.codigo_barras,
                )
            )
            criados += 1

        nota.compra_id = compra.id
        nota.status = "compra_gerada"
        nota.observacao = observacao or nota.observacao

        db.add(
            NotaImportacaoLog(
                nota_recebida_id=nota.id,
                usuario_id=usuario_id,
                tipo_evento="gerar_compra",
                mensagem=f"Compra #{compra.id} gerada a partir da nota.",
                payload_json={"compra_id": compra.id, "itens_criados": criados},
            )
        )

        db.commit()
        db.refresh(compra)
        db.refresh(nota)

        return NotaImportacaoGerarCompraResponse(
            nota_recebida_id=nota.id,
            compra_id=compra.id,
            status_nota=nota.status,
            status_compra=compra.status,
            itens_criados=criados,
            mensagem="Compra gerada com sucesso a partir da nota.",
        )

    def confirmar_compra(
        self,
        db: Session,
        *,
        nota_id: int,
        usuario_id: int,
        local_destino_id: int,
        origem: str = "nota_fiscal",
        observacao: str | None = None,
    ) -> NotaImportacaoConfirmarCompraResponse:
        nota = self._get_nota(db, nota_id)

        if nota.compra_id is None:
            raise ValueError("Esta nota ainda não possui compra gerada.")

        payload = CompraConfirmarRequest(
            local_destino_id=local_destino_id,
            origem=origem,
            observacao=observacao or f"Entrada via nota fiscal {nota.numero or nota.chave_acesso}",
        )

        resposta = self.compras_service.confirmar(db, nota.compra_id, payload)

        nota.status = "importada"
        db.add(
            NotaImportacaoLog(
                nota_recebida_id=nota.id,
                usuario_id=usuario_id,
                tipo_evento="confirmar_compra",
                mensagem=f"Compra #{nota.compra_id} confirmada com sucesso.",
                payload_json={"movimentacoes_criadas": resposta.movimentacoes_criadas},
            )
        )
        db.commit()
        db.refresh(nota)

        return NotaImportacaoConfirmarCompraResponse(
            nota_recebida_id=nota.id,
            compra_id=nota.compra_id,
            status_nota=nota.status,
            status_compra=resposta.status,
            movimentacoes_criadas=resposta.movimentacoes_criadas,
            mensagem="Compra confirmada e estoque atualizado com sucesso.",
        )

    def preview(self, db: Session, *, nota_id: int) -> dict:
        nota = self._get_nota(db, nota_id)
        itens = db.execute(
            select(NotaRecebidaItem).where(NotaRecebidaItem.nota_recebida_id == nota_id)
        ).scalars().all()

        rows = []
        prontos = 0
        pendentes = 0
        ignorados = 0

        for item in itens:
            fator = self._resolve_fator(db, item.id)
            pronto = (
                item.status_conciliacao == "vinculado"
                and item.produto_id is not None
                and item.unidade_informada_id is not None
            )

            if item.status_conciliacao == "ignorado":
                ignorados += 1
            elif pronto:
                prontos += 1
            else:
                pendentes += 1

            rows.append(
                {
                    "item_id": item.id,
                    "numero_item": item.numero_item,
                    "descricao": item.descricao,
                    "codigo_barras": item.codigo_barras,
                    "quantidade": item.quantidade,
                    "valor_unitario": item.valor_unitario,
                    "valor_total": item.valor_total,
                    "produto_id": item.produto_id,
                    "embalagem_id": item.embalagem_id,
                    "unidade_informada_id": item.unidade_informada_id,
                    "lote_id": item.lote_id,
                    "fator_para_base": fator,
                    "acao": item.status_conciliacao,
                    "validado": pronto,
                    "pronto_para_importar": pronto,
                    "observacao": item.observacao,
                }
            )

        compra_gerada = nota.compra_id is not None
        compra_confirmada = nota.status == "importada"

        return {
            "nota_recebida_id": nota.id,
            "fornecedor_id": nota.fornecedor_id,
            "fornecedor_nome": nota.fornecedor_nome or "",
            "fornecedor_cnpj": nota.fornecedor_cnpj,
            "numero": nota.numero,
            "serie": nota.serie,
            "chave_acesso": nota.chave_acesso,
            "total_itens": len(itens),
            "itens_prontos": prontos,
            "itens_pendentes": pendentes,
            "itens_ignorados": ignorados,
            "valor_total_nota": nota.valor_total,
            "compra_gerada": compra_gerada,
            "compra_confirmada": compra_confirmada,
            "compra_id": nota.compra_id,
            "status_nota": nota.status,
            "itens": rows,
        }

    def _resolve_fator(self, db: Session, item_id: int) -> float:
        from app.models.nota_conciliacao_item import NotaConciliacaoItem

        conciliacao = db.execute(
            select(NotaConciliacaoItem).where(NotaConciliacaoItem.nota_recebida_item_id == item_id)
        ).scalar_one_or_none()

        if conciliacao and conciliacao.fator_para_base:
            return float(conciliacao.fator_para_base)

        return 1.0

    def _get_nota(self, db: Session, nota_id: int) -> NotaRecebida:
        nota = db.get(NotaRecebida, nota_id)
        if not nota:
            raise ValueError("Nota recebida não encontrada.")
        return nota