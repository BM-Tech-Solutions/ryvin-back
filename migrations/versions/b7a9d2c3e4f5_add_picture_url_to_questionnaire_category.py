"""Add picture_url to questionnaire_category

Revision ID: b7a9d2c3e4f5
Revises: a1b2c3d4e5f6
Create Date: 2025-08-15 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7a9d2c3e4f5"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add picture_url (nullable) to questionnaire_category."""
    # Add as nullable to avoid issues with existing rows
    op.add_column(
        "questionnaire_category",
        sa.Column("picture_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema: drop picture_url from questionnaire_category."""
    op.drop_column("questionnaire_category", "picture_url")
