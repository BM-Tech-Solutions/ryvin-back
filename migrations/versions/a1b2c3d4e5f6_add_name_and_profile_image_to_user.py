"""add name and profile_image columns to user

Revision ID: a1b2c3d4e5f6
Revises: 3eb4cac67bf8
Create Date: 2025-08-10 14:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "3eb4cac67bf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns matching app.models.user.User
    op.add_column("user", sa.Column("name", sa.String(), nullable=True))
    op.add_column("user", sa.Column("profile_image", sa.String(), nullable=True))

    # Create unique indexes as per model (unique=True, index=True)
    op.create_index(op.f("ix_user_name"), "user", ["name"], unique=True)
    op.create_index(op.f("ix_user_profile_image"), "user", ["profile_image"], unique=True)

    # Make phone_number nullable to support Google-auth users without phones
    op.alter_column("user", "phone_number", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Drop indexes then columns
    op.drop_index(op.f("ix_user_profile_image"), table_name="user")
    op.drop_index(op.f("ix_user_name"), table_name="user")
    op.drop_column("user", "profile_image")
    op.drop_column("user", "name")

    # Revert phone_number to NOT NULL
    op.alter_column("user", "phone_number", existing_type=sa.String(), nullable=False)
