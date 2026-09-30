"""Add admin-only notes to hotel rooms and room requests

Revision ID: c3a1f0d9e5b7
Revises: b7c4d1a90f23
Create Date: 2026-09-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3a1f0d9e5b7'
down_revision = 'b7c4d1a90f23'
branch_labels = None
depends_on = None


def upgrade():
    # Internal placement notes for the rooming admins. Unlike the existing
    # request notes (written by the staffer, sent to Uber) and room notes
    # (sent to the hotel), these never leave the app.
    op.add_column('hotel_room_request', sa.Column(
        'admin_notes', sa.String(), nullable=True))
    op.add_column('hotel_room', sa.Column(
        'admin_notes', sa.String(), nullable=True))


def downgrade():
    op.drop_column('hotel_room', 'admin_notes')
    op.drop_column('hotel_room_request', 'admin_notes')
