"""initial backend schema placeholder

Revision ID: 0001_initial_backend
Revises:
Create Date: 2026-04-11 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision = "0001_initial_backend"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    # Use Alembic autogenerate after the first run if you want fully expanded table DDL.
    pass


def downgrade() -> None:
    pass
