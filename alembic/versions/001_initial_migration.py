"""Initial migration - create cows, sensors, and measurements tables

Revision ID: 001
Revises:
Create Date: 2025-11-26

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create cows table
    op.create_table(
        "cows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("birthdate", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cows_name"), "cows", ["name"], unique=False)

    # Create sensors table
    op.create_table(
        "sensors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("unit", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create measurements table
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sensor_id", sa.String(length=36), nullable=False),
        sa.Column("cow_id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cow_id"],
            ["cows.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["sensors.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_measurements_cow_id"), "measurements", ["cow_id"], unique=False
    )
    op.create_index(
        op.f("ix_measurements_sensor_id"), "measurements", ["sensor_id"], unique=False
    )
    op.create_index(
        op.f("ix_measurements_timestamp"), "measurements", ["timestamp"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_measurements_timestamp"), table_name="measurements")
    op.drop_index(op.f("ix_measurements_sensor_id"), table_name="measurements")
    op.drop_index(op.f("ix_measurements_cow_id"), table_name="measurements")
    op.drop_table("measurements")
    op.drop_table("sensors")
    op.drop_index(op.f("ix_cows_name"), table_name="cows")
    op.drop_table("cows")
