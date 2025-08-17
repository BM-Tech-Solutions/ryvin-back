"""Merge heads a54aac915e02 and b7a9d2c3e4f5

Revision ID: c0ffee123456
Revises: a54aac915e02, b7a9d2c3e4f5
Create Date: 2025-08-17 11:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa  # noqa: F401
from alembic import op  # noqa: F401  (kept for consistency and future edits)

# revision identifiers, used by Alembic.
revision: str = "c0ffee123456"
# This merge migration depends on both heads to unify the history
down_revision: Union[str, Sequence[str], None] = ("a54aac915e02", "b7a9d2c3e4f5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op merge: unify multiple heads into a single lineage."""
    pass


def downgrade() -> None:
    """No-op downgrade: nothing to undo for a merge."""
    pass
