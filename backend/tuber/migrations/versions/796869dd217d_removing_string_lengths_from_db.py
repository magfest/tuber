"""Removing string lengths from db

Revision ID: 796869dd217d
Revises: 4d2fcbec3fc3
Create Date: 2021-11-11 15:53:38.360332

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql
from tuber.models import BackgroundJob

# revision identifiers, used by Alembic.
revision = '796869dd217d'
down_revision = '4d2fcbec3fc3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    jobs = session.query(BackgroundJob).all()
    results = {}
    for job in jobs:
        results[job['id']] = job['result']
    with op.batch_alter_table('background_job', schema=None) as batch_op:
        batch_op.drop_column('result')
        batch_op.add_column(sa.Column('result', sa.LargeBinary()))
    jobs = session.query(BackgroundJob).all()
    for job in jobs:
        if job['id'] in results:
            job['result'] = results[job['id']]
            session.add(job)
    session.commit()

    with op.batch_alter_table('email_trigger', schema=None) as batch_op:
        batch_op.alter_column('context',
               existing_type=sa.VARCHAR(length=4096),
               type_=sa.JSON(),
               existing_nullable=True,
               postgresql_using="context::json")

    with op.batch_alter_table('schedule_event', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('shift', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('shift_signup', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               type_=sa.Integer(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('shift_signup', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=sa.Integer(),
               type_=postgresql.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)

    with op.batch_alter_table('shift', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=sa.Integer(),
               type_=postgresql.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)

    with op.batch_alter_table('schedule_event', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=sa.Integer(),
               type_=postgresql.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)

    with op.batch_alter_table('email_trigger', schema=None) as batch_op:
        batch_op.alter_column('context',
               existing_type=sa.JSON(),
               type_=sa.VARCHAR(length=4096),
               existing_nullable=True)

    with op.batch_alter_table('background_job', schema=None) as batch_op:
        batch_op.alter_column('result',
               existing_type=sa.LargeBinary(),
               type_=postgresql.JSON(astext_type=sa.Text()),
               existing_nullable=True)

    # ### end Alembic commands ###
