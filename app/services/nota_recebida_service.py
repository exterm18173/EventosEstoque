from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.certificado_fiscal import CertificadoFiscal
from app.models.fornecedores import Fornecedor
from app.models.nota_importacao_log import NotaImportacaoLog
from app.models.nota_recebida import NotaRecebida
from app.models.nota_recebida_item import NotaRecebidaItem
from app.schemas.nota_recebida import NotaRecebidaCreate, NotaRecebidaStatusUpdate


class NotaRecebidaService:
    def list(
        self,
        db: Session,
        *,
        certificado_fiscal_id: Optional[int] = None,
        fornecedor_id: Optional[int] = None,
        fornecedor_nome: Optional[str] = None,
        fornecedor_cnpj: Optional[str] = None,
        chave_acesso: Optional[str] = None,
        numero: Optional[str] = None,
        serie: Optional[str] = None,
        modelo: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[NotaRecebida]:
        stmt = select(NotaRecebida)

        if certificado_fiscal_id is not None:
            stmt = stmt.where(NotaRecebida.certificado_fiscal_id == certificado_fiscal_id)

        if fornecedor_id is not None:
            stmt = stmt.where(NotaRecebida.fornecedor_id == fornecedor_id)

        if fornecedor_nome:
            stmt = stmt.where(NotaRecebida.fornecedor_nome.ilike(f"%{fornecedor_nome.strip()}%"))

        if fornecedor_cnpj:
            stmt = stmt.where(NotaRecebida.fornecedor_cnpj == self._only_digits(fornecedor_cnpj))

        if chave_acesso:
            stmt = stmt.where(NotaRecebida.chave_acesso == chave_acesso.strip())

        if numero:
            stmt = stmt.where(NotaRecebida.numero == numero.strip())

        if serie:
            stmt = stmt.where(NotaRecebida.serie == serie.strip())

        if modelo:
            stmt = stmt.where(NotaRecebida.modelo == modelo.strip())

        if status:
            stmt = stmt.where(NotaRecebida.status == status.strip())

        stmt = stmt.order_by(
            NotaRecebida.data_autorizacao.desc().nullslast(),
            NotaRecebida.created_at.desc(),
        )
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, nota_id: int) -> NotaRecebida:
        obj = db.execute(
            select(NotaRecebida)
            .options(
                selectinload(NotaRecebida.itens),
                selectinload(NotaRecebida.logs),
            )
            .where(NotaRecebida.id == nota_id)
        ).scalar_one_or_none()

        if not obj:
            raise ValueError("Nota recebida não encontrada.")
        return obj

    def get_by_chave(self, db: Session, chave_acesso: str) -> Optional[NotaRecebida]:
        return db.execute(
            select(NotaRecebida).where(NotaRecebida.chave_acesso == chave_acesso.strip())
        ).scalar_one_or_none()

    def create(self, db: Session, data: NotaRecebidaCreate) -> NotaRecebida:
        if not db.get(CertificadoFiscal, data.certificado_fiscal_id):
            raise ValueError("Certificado fiscal inválido.")

        existente = self.get_by_chave(db, data.chave_acesso)
        if existente:
            raise ValueError("Já existe nota cadastrada com esta chave de acesso.")

        fornecedor_id = data.fornecedor_id
        if fornecedor_id is None and data.fornecedor_cnpj:
            fornecedor = self._find_or_create_fornecedor(
                db,
                nome=data.fornecedor_nome,
                documento=data.fornecedor_cnpj,
            )
            fornecedor_id = fornecedor.id

        obj = NotaRecebida(
            certificado_fiscal_id=data.certificado_fiscal_id,
            fornecedor_id=fornecedor_id,
            compra_id=data.compra_id,
            chave_acesso=data.chave_acesso.strip(),
            numero=data.numero.strip() if data.numero else None,
            serie=data.serie.strip() if data.serie else None,
            modelo=data.modelo.strip() if data.modelo else None,
            fornecedor_nome=data.fornecedor_nome.strip(),
            fornecedor_cnpj=self._only_digits(data.fornecedor_cnpj) if data.fornecedor_cnpj else None,
            natureza_operacao=data.natureza_operacao.strip() if data.natureza_operacao else None,
            cfop_predominante=data.cfop_predominante.strip() if data.cfop_predominante else None,
            data_emissao=self._coerce_datetime(data.data_emissao),
            data_autorizacao=self._coerce_datetime(data.data_autorizacao),
            valor_total=data.valor_total,
            valor_produtos=data.valor_produtos,
            valor_frete=data.valor_frete,
            valor_desconto=data.valor_desconto,
            valor_outros=data.valor_outros,
            protocolo=data.protocolo.strip() if data.protocolo else None,
            nsu=data.nsu.strip() if data.nsu else None,
            status=data.status.strip(),
            xml_path=data.xml_path,
            xml_hash=data.xml_hash,
            observacao=data.observacao,
            importada_em=self._coerce_datetime(data.importada_em),
        )
        db.add(obj)
        db.flush()

        for item in data.itens:
            db.add(
                NotaRecebidaItem(
                    nota_recebida_id=obj.id,
                    numero_item=item.numero_item,
                    codigo_fornecedor=item.codigo_fornecedor.strip() if item.codigo_fornecedor else None,
                    codigo_barras=item.codigo_barras.strip() if item.codigo_barras else None,
                    descricao=item.descricao.strip(),
                    ncm=item.ncm.strip() if item.ncm else None,
                    cfop=item.cfop.strip() if item.cfop else None,
                    unidade_comercial=item.unidade_comercial.strip() if item.unidade_comercial else None,
                    quantidade=float(item.quantidade),
                    valor_unitario=item.valor_unitario,
                    valor_total=item.valor_total,
                    produto_id=item.produto_id,
                    embalagem_id=item.embalagem_id,
                    unidade_informada_id=item.unidade_informada_id,
                    lote_id=item.lote_id,
                    status_conciliacao=item.status_conciliacao,
                    observacao=item.observacao,
                )
            )

        self._log(
            db,
            nota_recebida_id=obj.id,
            tipo_evento="criacao",
            mensagem="Nota recebida cadastrada.",
        )

        db.commit()
        db.refresh(obj)
        return obj

    def update_status(self, db: Session, nota_id: int, data: NotaRecebidaStatusUpdate) -> NotaRecebida:
        obj = self.get(db, nota_id)
        obj.status = data.status.strip()
        if data.observacao is not None:
            obj.observacao = data.observacao.strip() if data.observacao else None

        self._log(
            db,
            nota_recebida_id=obj.id,
            tipo_evento="status",
            mensagem=f"Status alterado para '{obj.status}'.",
        )

        db.commit()
        db.refresh(obj)
        return obj

    def ignorar(self, db: Session, nota_id: int, *, observacao: str | None = None) -> NotaRecebida:
        obj = self.get(db, nota_id)
        obj.status = "ignorada"
        if observacao is not None:
            obj.observacao = observacao.strip() if observacao else None

        self._log(
            db,
            nota_recebida_id=obj.id,
            tipo_evento="ignorar",
            mensagem="Nota marcada como ignorada.",
        )

        db.commit()
        db.refresh(obj)
        return obj

    def marcar_processada(self, db: Session, nota: NotaRecebida) -> None:
        nota.status = "processada"
        db.commit()

    def attach_compra(self, db: Session, nota: NotaRecebida, compra_id: int) -> None:
        nota.compra_id = compra_id
        nota.status = "compra_gerada"
        db.commit()

    def marcar_importada(self, db: Session, nota: NotaRecebida) -> None:
        nota.status = "importada"
        nota.importada_em = datetime.utcnow()
        db.commit()

    def _find_or_create_fornecedor(self, db: Session, *, nome: str, documento: str) -> Fornecedor:
        documento = self._only_digits(documento)
        fornecedor = db.execute(
            select(Fornecedor).where(Fornecedor.documento == documento)
        ).scalar_one_or_none()

        if fornecedor:
            return fornecedor

        fornecedor = Fornecedor(
            nome=nome.strip(),
            documento=documento,
        )
        db.add(fornecedor)
        db.flush()
        return fornecedor

    def _log(self, db: Session, *, nota_recebida_id: int, tipo_evento: str, mensagem: str) -> None:
        db.add(
            NotaImportacaoLog(
                nota_recebida_id=nota_recebida_id,
                tipo_evento=tipo_evento,
                mensagem=mensagem,
            )
        )

    def _only_digits(self, value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())

    def _coerce_datetime(self, value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None
        return None