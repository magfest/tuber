"""AdDropping unique constraint on badge types and ribbonns

Revision ID: 091e98f942c5
Revises: 6be1d8f61589
Create Date: 2021-11-15 23:03:56.931918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '091e98f942c5'
down_revision = '6be1d8f61589'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('badge_type', schema=None) as batch_op:
        batch_op.drop_constraint('badge_type_name_key', type_='unique')

    with op.batch_alter_table('ribbon_type', schema=None) as batch_op:
        batch_op.drop_constraint('ribbon_type_name_key', type_='unique')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ribbon_type', schema=None) as batch_op:
        batch_op.create_unique_constraint('ribbon_type_name_key', ['name'])

    with op.batch_alter_table('badge_type', schema=None) as batch_op:
        batch_op.create_unique_constraint('badge_type_name_key', ['name'])

    # ### end Alembic commands ###
