"""Storing uber details in db

Revision ID: 44ea59b15fb5
Revises: 53a92676ee86
Create Date: 2024-08-14 23:21:56.243589

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44ea59b15fb5'
down_revision = '53a92676ee86'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uber_url', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('uber_apikey', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('uber_slug', sa.String(), nullable=True))

    with op.batch_alter_table('hotel_location', schema=None) as batch_op:
        batch_op.drop_constraint('event_fk', type_='foreignkey')

    with op.batch_alter_table('hotel_room_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uber_id', sa.String(), nullable=True))
        batch_op.drop_column('approved')
        batch_op.drop_column('requested')
        batch_op.drop_column('assigned')

    with op.batch_alter_table('permission', schema=None) as batch_op:
        batch_op.drop_constraint('permission_operation_key', type_='unique')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('permission', schema=None) as batch_op:
        batch_op.create_unique_constraint('permission_operation_key', ['operation'])

    with op.batch_alter_table('hotel_room_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned', sa.BOOLEAN(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('requested', sa.BOOLEAN(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('approved', sa.BOOLEAN(), autoincrement=False, nullable=True))
        batch_op.drop_column('uber_id')

    with op.batch_alter_table('hotel_location', schema=None) as batch_op:
        batch_op.create_foreign_key('event_fk', 'event', ['event'], ['id'])

    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.drop_column('uber_slug')
        batch_op.drop_column('uber_apikey')
        batch_op.drop_column('uber_url')

    # ### end Alembic commands ###