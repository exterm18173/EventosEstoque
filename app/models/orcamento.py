from sqlalchemy import Integer, String, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Orcamento(Base, TimestampMixin):
    __tablename__ = "orcamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True, index=True)
    evento_id: Mapped[int | None] = mapped_column(ForeignKey("eventos.id"), nullable=True, index=True)

    data_saida_prevista: Mapped[Date | None] = mapped_column(Date, nullable=True)
    data_devolucao_prevista: Mapped[Date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        String(30),
        default="rascunho",
        nullable=False,
        index=True,
    )  # rascunho|enviado|aprovado|reprovado|convertido|cancelado

    valor_total: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relacionamentos
    itens = relationship(
        "OrcamentoItem",
        back_populates="orcamento",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrcamentoItem(Base, TimestampMixin):
    __tablename__ = "orcamento_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orcamento_id: Mapped[int] = mapped_column(ForeignKey("orcamentos.id"), nullable=False, index=True)

    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)

    quantidade_base: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    valor_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    orcamento = relationship("Orcamento", back_populates="itens")
