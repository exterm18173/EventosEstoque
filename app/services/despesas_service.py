from __future__ import annotations

import csv
import io
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from fastapi import UploadFile

from app.models.despesas import Despesa 
from app.models.eventos import Evento
from app.schemas.despesas import DespesaCreate, DespesaUpdate, DespesaImportResult
from app.schemas.despesas_relatorio import DespesaResumoResponse, DespesaResumoRow


def _parse_date_br(value: str) -> date | None:
    if not value:
        return None
    v = value.strip()
    # aceita YYYY-MM-DD ou DD/MM/YYYY
    try:
        if "-" in v:
            return date.fromisoformat(v[:10])
        if "/" in v:
            dd, mm, yyyy = v.split("/")
            return date(int(yyyy), int(mm), int(dd))
    except Exception:
        return None
    return None


def _to_float(value: str) -> float | None:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    # "1.234,56" -> "1234.56"
    v = v.replace(".", "").replace(",", ".")
    try:
        return float(v)
    except Exception:
        return None


class DespesasService:
    def list(
        self,
        db: Session,
        *,
        evento_id: int | None = None,
        categoria: str | None = None,
        data_inicio: str | None = None,  # YYYY-MM-DD
        data_fim: str | None = None,
        q: str | None = None,
    ) -> list[Despesa]:
        stmt = select(Despesa)

        if evento_id is not None:
            stmt = stmt.where(Despesa.evento_id == evento_id)
        if categoria is not None:
            stmt = stmt.where(Despesa.categoria == categoria)

        if data_inicio:
            stmt = stmt.where(Despesa.data >= data_inicio)
        if data_fim:
            stmt = stmt.where(Despesa.data <= data_fim)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Despesa.descricao.ilike(like))

        stmt = stmt.order_by(Despesa.data.desc(), Despesa.id.desc())
        return list(db.execute(stmt).scalars().all())

    def get(self, db: Session, despesa_id: int) -> Despesa:
        obj = db.get(Despesa, despesa_id)
        if not obj:
            raise ValueError("Despesa não encontrada.")
        return obj

    def create(self, db: Session, data: DespesaCreate) -> Despesa:
        if data.evento_id is not None and not db.get(Evento, data.evento_id):
            raise ValueError("Evento inválido.")

        obj = Despesa(
            data=data.data,
            descricao=data.descricao.strip(),
            valor=float(data.valor),
            categoria=(data.categoria.strip() if data.categoria else None),
            forma_pagamento=(data.forma_pagamento.strip() if data.forma_pagamento else None),
            fornecedor_nome=(data.fornecedor_nome.strip() if data.fornecedor_nome else None),
            documento_ref=(data.documento_ref.strip() if data.documento_ref else None),
            evento_id=data.evento_id,
            observacao=data.observacao,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, despesa_id: int, data: DespesaUpdate) -> Despesa:
        obj = self.get(db, despesa_id)

        if data.evento_id is not None or "evento_id" in data.model_fields_set:
            if data.evento_id is not None and not db.get(Evento, data.evento_id):
                raise ValueError("Evento inválido.")
            obj.evento_id = data.evento_id

        if data.data is not None:
            obj.data = data.data
        if data.descricao is not None:
            obj.descricao = data.descricao.strip()
        if data.valor is not None:
            obj.valor = float(data.valor)

        if data.categoria is not None or "categoria" in data.model_fields_set:
            obj.categoria = data.categoria.strip() if data.categoria else None
        if data.forma_pagamento is not None or "forma_pagamento" in data.model_fields_set:
            obj.forma_pagamento = data.forma_pagamento.strip() if data.forma_pagamento else None

        if data.fornecedor_nome is not None or "fornecedor_nome" in data.model_fields_set:
            obj.fornecedor_nome = data.fornecedor_nome.strip() if data.fornecedor_nome else None
        if data.documento_ref is not None or "documento_ref" in data.model_fields_set:
            obj.documento_ref = data.documento_ref.strip() if data.documento_ref else None

        if data.observacao is not None or "observacao" in data.model_fields_set:
            obj.observacao = data.observacao

        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, despesa_id: int) -> None:
        obj = self.get(db, despesa_id)
        db.delete(obj)
        db.commit()

    def importar_csv(self, db: Session, file: UploadFile) -> DespesaImportResult:
        content = file.file.read()
        if not content:
            raise ValueError("CSV vazio.")

        # tenta decodificar em utf-8 (MVP)
        try:
            text = content.decode("utf-8-sig")
        except Exception:
            text = content.decode("latin1")

        reader = csv.DictReader(io.StringIO(text))

        recebidas = 0
        importadas = 0
        ignoradas = 0
        erros: list[str] = []

        # esperado: data,descricao,valor,categoria,forma_pagamento,fornecedor_nome,documento_ref,evento_id
        for idx, row in enumerate(reader, start=2):  # 1 é header
            recebidas += 1
            dt = _parse_date_br(row.get("data", ""))
            desc = (row.get("descricao") or "").strip()
            val = _to_float(row.get("valor", ""))

            if not dt or not desc or not val or val <= 0:
                ignoradas += 1
                erros.append(f"Linha {idx}: inválida (data/descricao/valor).")
                continue

            cat = (row.get("categoria") or "").strip() or None
            fp = (row.get("forma_pagamento") or "").strip() or None
            forn = (row.get("fornecedor_nome") or "").strip() or None
            docref = (row.get("documento_ref") or "").strip() or None

            evento_id = row.get("evento_id")
            ev_id = None
            if evento_id:
                try:
                    ev_id = int(str(evento_id).strip())
                    if not db.get(Evento, ev_id):
                        erros.append(f"Linha {idx}: evento_id {ev_id} não existe (ignorando vínculo).")
                        ev_id = None
                except Exception:
                    erros.append(f"Linha {idx}: evento_id inválido (ignorando vínculo).")
                    ev_id = None

            obj = Despesa(
                data=dt,
                descricao=desc,
                valor=float(val),
                categoria=cat,
                forma_pagamento=fp,
                fornecedor_nome=forn,
                documento_ref=docref,
                evento_id=ev_id,
            )
            db.add(obj)
            importadas += 1

        db.commit()
        return DespesaImportResult(
            linhas_recebidas=recebidas,
            linhas_importadas=importadas,
            linhas_ignoradas=ignoradas,
            erros=erros[:200],
        )

    def resumo(self, db: Session, *, agrupamento: str, inicio: str | None, fim: str | None, evento_id: int | None) -> DespesaResumoResponse:
        if agrupamento not in {"periodo", "categoria", "evento"}:
            raise ValueError("Agrupamento inválido. Use: periodo|categoria|evento.")

        stmt = select(Despesa)

        if inicio:
            stmt = stmt.where(Despesa.data >= inicio)
        if fim:
            stmt = stmt.where(Despesa.data <= fim)
        if evento_id is not None:
            stmt = stmt.where(Despesa.evento_id == evento_id)

        if agrupamento == "categoria":
            q = select(
                func.coalesce(Despesa.categoria, "sem_categoria").label("k"),
                func.sum(Despesa.valor).label("total"),
            )
            q = q.select_from(Despesa)
            if inicio:
                q = q.where(Despesa.data >= inicio)
            if fim:
                q = q.where(Despesa.data <= fim)
            if evento_id is not None:
                q = q.where(Despesa.evento_id == evento_id)
            q = q.group_by("k").order_by(func.sum(Despesa.valor).desc())

            rows = [DespesaResumoRow(chave=r.k, total=float(r.total or 0)) for r in db.execute(q).all()]
            return DespesaResumoResponse(agrupamento="categoria", inicio=inicio, fim=fim, rows=rows)

        if agrupamento == "evento":
            q = select(
                func.coalesce(func.cast(Despesa.evento_id, str), "sem_evento").label("k"),
                func.sum(Despesa.valor).label("total"),
            ).select_from(Despesa)
            if inicio:
                q = q.where(Despesa.data >= inicio)
            if fim:
                q = q.where(Despesa.data <= fim)
            if evento_id is not None:
                q = q.where(Despesa.evento_id == evento_id)
            q = q.group_by("k").order_by(func.sum(Despesa.valor).desc())

            rows = [DespesaResumoRow(chave=f"evento:{r.k}", total=float(r.total or 0)) for r in db.execute(q).all()]
            return DespesaResumoResponse(agrupamento="evento", inicio=inicio, fim=fim, rows=rows)

        # periodo (YYYY-MM)
        q = select(
            func.to_char(Despesa.data, "YYYY-MM").label("k"),
            func.sum(Despesa.valor).label("total"),
        ).select_from(Despesa)
        if inicio:
            q = q.where(Despesa.data >= inicio)
        if fim:
            q = q.where(Despesa.data <= fim)
        if evento_id is not None:
            q = q.where(Despesa.evento_id == evento_id)
        q = q.group_by("k").order_by("k")

        rows = [DespesaResumoRow(chave=r.k, total=float(r.total or 0)) for r in db.execute(q).all()]
        return DespesaResumoResponse(agrupamento="periodo", inicio=inicio, fim=fim, rows=rows)
