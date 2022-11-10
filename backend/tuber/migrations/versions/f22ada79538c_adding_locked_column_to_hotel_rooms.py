"""Adding locked column to hotel_rooms

Revision ID: f22ada79538c
Revises: 844962e6352c
Create Date: 2021-11-22 02:56:52.275043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f22ada79538c'
down_revision = '844962e6352c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locked', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.drop_column('locked')

    # ### end Alembic commands ###