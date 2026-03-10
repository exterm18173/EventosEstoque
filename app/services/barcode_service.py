from fastapi import Request
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.estoque_saldos import EstoqueSaldo
from app.models.produto_codigos_barras import ProdutoCodigoBarras
from app.models.produto_embalagens import ProdutoEmbalagem
from app.models.produtos import Produto
from app.models.unidades import Unidade
from app.schemas.barcode import BarcodeLookupResponse


class BarcodeService:
    def lookup(
        self,
        db: Session,
        codigo: str,
        request: Request,
        local_id: int | None = None,
    ) -> BarcodeLookupResponse:
        code = (codigo or "").strip()
        if not code:
            raise ValueError("Código de barras vazio.")

        cb = db.execute(
            select(ProdutoCodigoBarras).where(
                ProdutoCodigoBarras.codigo == code,
                ProdutoCodigoBarras.ativo == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if not cb:
            raise ValueError("Código de barras não encontrado.")

        produto = db.get(Produto, cb.produto_id)
        if not produto or not produto.ativo:
            raise ValueError("Produto do código de barras não encontrado.")

        return self._build_lookup_response(
            db=db,
            request=request,
            produto=produto,
            codigo=code,
            embalagem_id=cb.embalagem_id,
            local_id=local_id,
        )

    def buscar_por_nome(
        self,
        db: Session,
        request: Request,
        q: str,
        limit: int = 20,
        local_id: int | None = None,
    ) -> list[BarcodeLookupResponse]:
        termo = (q or "").strip()
        if not termo:
            raise ValueError("Informe um nome para busca.")

        stmt = (
            select(Produto)
            .options(
                selectinload(Produto.embalagens).selectinload(ProdutoEmbalagem.unidade),
                selectinload(Produto.codigos_barras),
                selectinload(Produto.unidade_base),
            )
            .where(
                Produto.ativo == True,  # noqa: E712
                or_(
                    Produto.nome_comercial.ilike(f"%{termo}%"),
                    and_(
                        Produto.sku.is_not(None),
                        Produto.sku.ilike(f"%{termo}%"),
                    ),
                ),
            )
            .order_by(Produto.nome_comercial.asc())
            .limit(limit)
        )

        produtos = db.execute(stmt).scalars().unique().all()

        return [
            self._build_lookup_response_from_produto(
                db=db,
                request=request,
                produto=produto,
                local_id=local_id,
            )
            for produto in produtos
        ]

    def _build_lookup_response_from_produto(
        self,
        db: Session,
        request: Request,
        produto: Produto,
        local_id: int | None = None,
    ) -> BarcodeLookupResponse:
        embalagem = self._pick_embalagem(produto)
        codigo = self._pick_codigo(produto, embalagem.id if embalagem else None)
        saldo_base = self._get_saldo_base(db, produto.id, local_id)
        foto_url = self._build_foto_url(request, produto.foto_path)

        if embalagem:
            unidade_emb = embalagem.unidade or db.get(Unidade, embalagem.unidade_id)
            if not unidade_emb:
                raise ValueError("Unidade da embalagem não encontrada.")

            return BarcodeLookupResponse(
                codigo=codigo,
                produto_id=produto.id,
                produto_nome=produto.nome_comercial,
                embalagem_id=embalagem.id,
                embalagem_nome=embalagem.nome,
                unidade_informada_id=unidade_emb.id,
                unidade_sigla=unidade_emb.sigla,
                fator_para_base=float(embalagem.fator_para_base),
                saldo_local_id=local_id,
                saldo_base=saldo_base,
                foto_url=foto_url,
                foto_mime=produto.foto_mime,
                foto_nome_original=produto.foto_nome_original,
            )

        unidade_base = produto.unidade_base or db.get(Unidade, produto.unidade_base_id)
        if not unidade_base:
            raise ValueError("Unidade base do produto não encontrada.")

        return BarcodeLookupResponse(
            codigo=codigo,
            produto_id=produto.id,
            produto_nome=produto.nome_comercial,
            embalagem_id=None,
            embalagem_nome=None,
            unidade_informada_id=unidade_base.id,
            unidade_sigla=unidade_base.sigla,
            fator_para_base=1.0,
            saldo_local_id=local_id,
            saldo_base=saldo_base,
            foto_url=foto_url,
            foto_mime=produto.foto_mime,
            foto_nome_original=produto.foto_nome_original,
        )

    def _build_lookup_response(
        self,
        db: Session,
        request: Request,
        produto: Produto,
        codigo: str | None,
        embalagem_id: int | None,
        local_id: int | None = None,
    ) -> BarcodeLookupResponse:
        unidade_base = db.get(Unidade, produto.unidade_base_id)
        if not unidade_base:
            raise ValueError("Unidade base do produto não encontrada.")

        saldo_base = self._get_saldo_base(db, produto.id, local_id)
        foto_url = self._build_foto_url(request, produto.foto_path)

        if embalagem_id:
            emb = db.get(ProdutoEmbalagem, embalagem_id)
            if not emb or emb.produto_id != produto.id:
                raise ValueError("Embalagem inválida para este produto.")

            uni_emb = db.get(Unidade, emb.unidade_id)
            if not uni_emb:
                raise ValueError("Unidade da embalagem não encontrada.")

            return BarcodeLookupResponse(
                codigo=codigo,
                produto_id=produto.id,
                produto_nome=produto.nome_comercial,
                embalagem_id=emb.id,
                embalagem_nome=emb.nome,
                unidade_informada_id=uni_emb.id,
                unidade_sigla=uni_emb.sigla,
                fator_para_base=float(emb.fator_para_base),
                saldo_local_id=local_id,
                saldo_base=saldo_base,
                foto_url=foto_url,
                foto_mime=produto.foto_mime,
                foto_nome_original=produto.foto_nome_original,
            )

        return BarcodeLookupResponse(
            codigo=codigo,
            produto_id=produto.id,
            produto_nome=produto.nome_comercial,
            embalagem_id=None,
            embalagem_nome=None,
            unidade_informada_id=unidade_base.id,
            unidade_sigla=unidade_base.sigla,
            fator_para_base=1.0,
            saldo_local_id=local_id,
            saldo_base=saldo_base,
            foto_url=foto_url,
            foto_mime=produto.foto_mime,
            foto_nome_original=produto.foto_nome_original,
        )

    def _build_foto_url(self, request: Request, foto_path: str | None) -> str | None:
        if not foto_path:
            return None

        path = foto_path.strip().replace("\\", "/")
        if not path:
            return None

        if path.startswith("http://") or path.startswith("https://"):
            return path

        if path.startswith("storage/"):
            path = path[len("storage/"):]
        elif path.startswith("/storage/"):
            path = path[len("/storage/"):]

        base_url = str(request.base_url).rstrip("/")
        return f"{base_url}/media/{path.lstrip('/')}"

    def _get_saldo_base(self, db: Session, produto_id: int, local_id: int | None) -> float | None:
        if not local_id:
            return None

        saldo = db.execute(
            select(EstoqueSaldo).where(
                EstoqueSaldo.produto_id == produto_id,
                EstoqueSaldo.local_id == local_id,
            )
        ).scalar_one_or_none()

        return 0.0 if not saldo else float(saldo.quantidade_base)

    def _pick_embalagem(self, produto: Produto) -> ProdutoEmbalagem | None:
        embalagens = list(produto.embalagens or [])
        if not embalagens:
            return None
        return next((e for e in embalagens if e.principal), None) or sorted(embalagens, key=lambda e: e.id or 0)[0]

    def _pick_codigo(self, produto: Produto, embalagem_id: int | None) -> str | None:
        codigos = [c for c in (produto.codigos_barras or []) if c.ativo]
        if not codigos:
            return None

        if embalagem_id is not None:
            cod_principal_emb = next(
                (c for c in codigos if c.embalagem_id == embalagem_id and c.principal),
                None,
            )
            if cod_principal_emb:
                return cod_principal_emb.codigo

            cod_emb = next((c for c in codigos if c.embalagem_id == embalagem_id), None)
            if cod_emb:
                return cod_emb.codigo

        cod_principal = next((c for c in codigos if c.principal), None)
        return cod_principal.codigo if cod_principal else codigos[0].codigo