"""Added completed column to hotel_room_request

Revision ID: 528cd10edcce
Revises: 72220252d424
Create Date: 2019-11-21 12:31:25.439090

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '528cd10edcce'
down_revision = '72220252d424'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.add_column(sa.Column('completed', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.drop_column('completed')

    # ### end Alembic commands ###