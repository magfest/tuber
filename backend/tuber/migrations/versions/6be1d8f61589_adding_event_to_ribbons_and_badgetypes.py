"""Adding event to ribbons and badgetypes

Revision ID: 6be1d8f61589
Revises: 4ae40638e863
Create Date: 2021-11-15 22:47:51.305551

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6be1d8f61589'
down_revision = '4ae40638e863'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('badge_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('event', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('ribbon_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('event', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ribbon_type', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('event')

    with op.batch_alter_table('badge_type', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('event')

    # ### end Alembic commands ###
