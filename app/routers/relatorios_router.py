from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.relatorios import (
    EstoqueSaldoResponse, EstoqueSaldoRow,
    MovimentacoesResponse, MovimentacaoRow,
    CustoEventoResponse,
)
from app.services.relatorios_service import RelatoriosService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])
service = RelatoriosService()


@router.get("/estoque", response_model=EstoqueSaldoResponse)
def estoque(
    produto_id: int | None = Query(default=None),
    local_id: int | None = Query(default=None),
    somente_positivos: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    rows = service.estoque(db, produto_id=produto_id, local_id=local_id, somente_positivos=somente_positivos)
    out = [
        EstoqueSaldoRow(
            produto_id=r.produto_id,
            produto_nome=r.produto_nome,
            local_id=r.local_id,
            local_nome=r.local_nome,
            quantidade_base=float(r.quantidade_base or 0.0),
        )
        for r in rows
    ]
    return EstoqueSaldoResponse(rows=out)


@router.get("/movimentacoes", response_model=MovimentacoesResponse)
def movimentacoes(
    data_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(default=None, description="YYYY-MM-DD"),
    tipo: str | None = Query(default=None),
    origem: str | None = Query(default=None),
    produto_id: int | None = Query(default=None),
    evento_id: int | None = Query(default=None),
    aluguel_id: int | None = Query(default=None),
    local_id: int | None = Query(default=None),
    limit: int = Query(default=300, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    rows = service.movimentacoes(
        db,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo=tipo,
        origem=origem,
        produto_id=produto_id,
        evento_id=evento_id,
        aluguel_id=aluguel_id,
        local_id=local_id,
        limit=limit,
    )

    out = [
        MovimentacaoRow(
            id=r.id,
            created_at=r.created_at.isoformat() if r.created_at else "",
            tipo=r.tipo,
            origem=r.origem,
            produto_id=r.produto_id,
            produto_nome=r.produto_nome,
            quantidade_informada=float(r.quantidade_informada or 0.0),
            unidade_informada_id=r.unidade_informada_id,
            fator_para_base=float(r.fator_para_base or 1.0),
            quantidade_base=float(r.quantidade_base or 0.0),
            custo_unitario=(float(r.custo_unitario) if r.custo_unitario is not None else None),
            evento_id=r.evento_id,
            aluguel_id=r.aluguel_id,
            local_origem_id=r.local_origem_id,
            local_destino_id=r.local_destino_id,
        )
        for r in rows
    ]
    return MovimentacoesResponse(rows=out)


@router.get("/custos_evento/{evento_id}", response_model=CustoEventoResponse)
def custos_evento(evento_id: int, db: Session = Depends(get_db)):
    try:
        despesas_total, consumo_total, total = service.custo_evento(db, evento_id)
        return CustoEventoResponse(
            evento_id=evento_id,
            despesas_total=despesas_total,
            consumo_estoque_total=consumo_total,
            total=total,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
