"""profissao opcional

Revision ID: 7f2a89ca807a
Revises: 
Create Date: 2026-07-27 14:29:07.503339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f2a89ca807a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('dentists', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dentists_cpf_hash'))
        batch_op.create_index(batch_op.f('ix_dentists_cpf_hash'), ['cpf_hash'], unique=False)

    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.alter_column('profession',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.alter_column('profession',
               existing_type=sa.VARCHAR(),
               nullable=False)

    with op.batch_alter_table('dentists', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dentists_cpf_hash'))
        batch_op.create_index(batch_op.f('ix_dentists_cpf_hash'), ['cpf_hash'], unique=True)
