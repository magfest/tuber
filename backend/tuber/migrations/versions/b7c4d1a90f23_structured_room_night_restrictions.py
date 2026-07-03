"""Structured room night restrictions and suggested rooms

Revision ID: b7c4d1a90f23
Revises: 28e0b36a0af8
Create Date: 2026-07-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c4d1a90f23'
down_revision = '28e0b36a0af8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('hotel_room_night', sa.Column(
        'restriction_mode', sa.String(), nullable=False, server_default='none'))
    op.add_column('hotel_room_night', sa.Column(
        'shift_hours_required', sa.Integer(), nullable=True))
    op.add_column('hotel_room', sa.Column(
        'suggested', sa.Boolean(), nullable=True, server_default='false'))
    # Existing restricted nights all used the shift-window behavior.
    op.execute(
        "UPDATE hotel_room_night SET restriction_mode = 'shift_window' "
        "WHERE restricted = true")


def downgrade():
    op.drop_column('hotel_room', 'suggested')
    op.drop_column('hotel_room_night', 'shift_hours_required')
    op.drop_column('hotel_room_night', 'restriction_mode')
