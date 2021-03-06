"""Refactoring

Revision ID: eca6792a5ab5
Revises: 0f768e57a051
Create Date: 2019-11-24 04:54:44.414567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eca6792a5ab5'
down_revision = '0f768e57a051'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    badge_types = op.create_table('badge_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('description', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('ribbon_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('description', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('ribbon_to_badge',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ribbon', sa.Integer(), nullable=True),
    sa.Column('badge', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['badge'], ['badge.id'], ),
    sa.ForeignKeyConstraint(['ribbon'], ['ribbon_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.bulk_insert(badge_types, [{'id': 1, 'name': 'Staff', 'description': 'Run the event.'}])
    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.add_column(sa.Column('badge_type', sa.Integer(), nullable=False, server_default='1'))
        batch_op.create_foreign_key("badge_badge_type_fkey", 'badge_type', ['badge_type'], ['id'])

    with op.batch_alter_table('room_night_approval', schema=None) as batch_op:
        batch_op.add_column(sa.Column('badge', sa.Integer()))

    op.execute('update room_night_approval set badge = (select badge from room_night_request where room_night_request.id = room_night_approval.room_night)')
    op.execute('update room_night_approval set room_night = (select room_night from room_night_request where room_night_request.id = room_night_approval.room_night)')
    
    with op.batch_alter_table('room_night_approval', schema=None) as batch_op:
        batch_op.create_foreign_key("room_night_approval_badge_fkey", 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key("room_night_approval_hotel_room_night_fkey", 'hotel_room_night', ['room_night'], ['id'])

    with op.batch_alter_table('room_night_request', schema=None) as batch_op:
        batch_op.alter_column('badge',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('room_night_request', schema=None) as batch_op:
        batch_op.alter_column('badge',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('room_night_approval', schema=None) as batch_op:
        batch_op.drop_constraint('room_night_approval_badge_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_approval_room_night_fkey', type_='foreignkey')

    op.execute('update room_night_approval set room_night=subquery.room_night from (select room_night_approval.id, room_night_request.room_night from room_night_request join room_night_approval on room_night_approval.badge = room_night_request.badge) as subquery where subquery.id=room_night_approval.id;')

    with op.batch_alter_table('room_night_approval', schema=None) as batch_op:
        batch_op.create_foreign_key('room_night_approval_room_night_request_fkey', 'room_night_request', ['room_night'], ['id'])
        batch_op.drop_column('badge')

    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.drop_constraint('badge_badge_type_fkey', type_='foreignkey')
        batch_op.drop_column('badge_type')

    op.drop_table('ribbon_to_badge')
    op.drop_table('ribbon_type')
    op.drop_table('badge_type')
    # ### end Alembic commands ###
