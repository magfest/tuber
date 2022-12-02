"""Make sure all foreignkeys either have a delete cascade or are nullable

Revision ID: cd6926818967
Revises: 5358d76ff848
Create Date: 2022-11-20 15:59:42.223606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd6926818967'
down_revision = '5358d76ff848'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('department_grant', schema=None) as batch_op:
        batch_op.drop_constraint('department_grant_user_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'user', ['user'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('department_grant', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('department_grant_user_fkey', 'user', ['user'], ['id'])

    # ### end Alembic commands ###