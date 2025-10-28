"""Agregar usuario_id a reserva

Revision ID: 7e48302742a3
Revises: 
Create Date: 2025-08-21 22:58:29.948130

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e48302742a3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Agrega la columna usuario_id a reserva de manera idempotente
    (no falla si ya existe) y crea la FK sólo si no está creada.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    columnas = [c['name'] for c in insp.get_columns('reserva')]
    if 'usuario_id' not in columnas:
        op.add_column('reserva', sa.Column('usuario_id', sa.Integer(), nullable=True))

    # Crear FK con nombre explícito para facilitar downgrade
    fk_name = 'fk_reserva_usuario_id'
    fks = insp.get_foreign_keys('reserva')
    fk_exists = any(
        fk.get('name') == fk_name or (fk.get('referred_table') == 'usuario' and fk.get('constrained_columns') == ['usuario_id'])
        for fk in fks
    )
    if not fk_exists:
        op.create_foreign_key(fk_name, 'reserva', 'usuario', ['usuario_id'], ['id'])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Eliminar FK si existe
    fk_name = 'fk_reserva_usuario_id'
    fks = insp.get_foreign_keys('reserva')
    if any(fk.get('name') == fk_name for fk in fks):
        op.drop_constraint(fk_name, 'reserva', type_='foreignkey')

    # Eliminar columna si existe
    columnas = [c['name'] for c in insp.get_columns('reserva')]
    if 'usuario_id' in columnas:
        op.drop_column('reserva', 'usuario_id')
