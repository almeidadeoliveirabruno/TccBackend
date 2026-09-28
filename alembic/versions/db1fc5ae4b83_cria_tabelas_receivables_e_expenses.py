"""cria tabelas receivables e expenses

Revision ID: db1fc5ae4b83
Revises: 05da4f2b936d
Create Date: 2026-08-09 16:53:57.421339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db1fc5ae4b83'
down_revision: Union[str, Sequence[str], None] = '05da4f2b936d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
