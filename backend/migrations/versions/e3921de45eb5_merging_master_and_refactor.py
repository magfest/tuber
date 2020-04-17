"""Merging master and refactor

Revision ID: e3921de45eb5
Revises: eca6792a5ab5, f1890659822f
Create Date: 2020-01-20 20:00:26.571086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3921de45eb5'
down_revision = ('eca6792a5ab5', 'f1890659822f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
