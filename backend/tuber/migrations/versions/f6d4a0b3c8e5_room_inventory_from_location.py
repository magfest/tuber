"""Copy each location's Uber inventory onto its rooms

Revision ID: f6d4a0b3c8e5
Revises: e5c3f9a2b7d4
Create Date: 2026-11-17 14:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f6d4a0b3c8e5'
down_revision = 'e5c3f9a2b7d4'
branch_labels = None
depends_on = None


def upgrade():
    # The export now reads only the room's own inventory. Rooms that relied
    # on their location's get it copied over, so they export as they did;
    # a room that already has its own keeps it.
    op.execute("""
        UPDATE hotel_room SET uber_inventory_id = hotel_location.uber_inventory_id
        FROM hotel_location
        WHERE hotel_room.hotel_location = hotel_location.id
          AND (hotel_room.uber_inventory_id IS NULL OR hotel_room.uber_inventory_id = '')
          AND hotel_location.uber_inventory_id IS NOT NULL
          AND hotel_location.uber_inventory_id != ''
    """)


def downgrade():
    # Nothing to undo: the copied values cannot be told from ones set by hand.
    pass
