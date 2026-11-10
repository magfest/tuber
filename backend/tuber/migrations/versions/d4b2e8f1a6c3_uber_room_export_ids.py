"""Add the Uber ids the room export needs

Revision ID: d4b2e8f1a6c3
Revises: c3a1f0d9e5b7
Create Date: 2026-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4b2e8f1a6c3'
down_revision = 'c3a1f0d9e5b7'
branch_labels = None
depends_on = None


def upgrade():
    # The Uber inventory block a location's rooms are exported into, the
    # Uber room assignment a room exports as, and a hash of what was sent.
    op.add_column('hotel_location', sa.Column(
        'uber_inventory_id', sa.String(), nullable=True))
    op.add_column('hotel_room', sa.Column(
        'uber_id', sa.String(), nullable=True))
    op.add_column('hotel_room', sa.Column(
        'uber_export_hash', sa.String(), nullable=True))


def downgrade():
    op.drop_column('hotel_room', 'uber_export_hash')
    op.drop_column('hotel_room', 'uber_id')
    op.drop_column('hotel_location', 'uber_inventory_id')
