"""Ajuste logica e estrutura de eventos

Revision ID: 811bc8e4dfb0
Revises: 7c58fded9b6e
Create Date: 2026-03-13 04:15:05.929238

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '811bc8e4dfb0'
down_revision = '7c58fded9b6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'eventos',
        sa.Column(
            'tipo_evento',
            sa.String(length=20),
            nullable=False,
            server_default='principal',
        ),
    )

    op.add_column('eventos', sa.Column('evento_pai_id', sa.Integer(), nullable=True))

    op.execute("UPDATE eventos SET tipo_evento = 'principal' WHERE tipo_evento IS NULL")

    op.create_index(op.f('ix_eventos_evento_pai_id'), 'eventos', ['evento_pai_id'], unique=False)
    op.create_index(op.f('ix_eventos_tipo_evento'), 'eventos', ['tipo_evento'], unique=False)

    op.create_foreign_key(
        'fk_eventos_evento_pai_id_eventos',
        'eventos',
        'eventos',
        ['evento_pai_id'],
        ['id'],
    )

    op.alter_column('eventos', 'tipo_evento', server_default=None)


def downgrade() -> None:
    op.drop_constraint('fk_eventos_evento_pai_id_eventos', 'eventos', type_='foreignkey')
    op.drop_index(op.f('ix_eventos_tipo_evento'), table_name='eventos')
    op.drop_index(op.f('ix_eventos_evento_pai_id'), table_name='eventos')
    op.drop_column('eventos', 'evento_pai_id')
    op.drop_column('eventos', 'tipo_evento')