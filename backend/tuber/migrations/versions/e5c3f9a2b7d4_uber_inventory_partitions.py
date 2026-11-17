"""Per-room Uber inventory and partition, and the lists imported from Uber

Revision ID: e5c3f9a2b7d4
Revises: d4b2e8f1a6c3
Create Date: 2026-11-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5c3f9a2b7d4'
down_revision = 'd4b2e8f1a6c3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('hotel_room', sa.Column(
        'uber_inventory_id', sa.String(), nullable=True))
    op.add_column('hotel_room', sa.Column(
        'uber_partition_id', sa.String(), nullable=True))
    op.create_table(
        'uber_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event', sa.Integer(), nullable=True),
        sa.Column('uber_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('hotel_name', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('modified', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['event'], ['event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'))
    op.create_table(
        'uber_partition',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event', sa.Integer(), nullable=True),
        sa.Column('uber_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('inventory_ids', sa.String(), nullable=True),
        sa.Column('created', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('modified', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['event'], ['event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('uber_partition')
    op.drop_table('uber_inventory')
    op.drop_column('hotel_room', 'uber_partition_id')
    op.drop_column('hotel_room', 'uber_inventory_id')
