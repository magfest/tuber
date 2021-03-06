"""Added shift management

Revision ID: 7a98a0c9fb44
Revises: 4affc388b48b
Create Date: 2020-05-22 16:43:21.650563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a98a0c9fb44'
down_revision = '4affc388b48b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('schedule',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('event', sa.Integer(), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['event'], ['event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('event', sa.Integer(), nullable=True),
    sa.Column('documentation', sa.String(), nullable=True),
    sa.Column('department', sa.Integer(), nullable=True),
    sa.Column('method', sa.JSON(), nullable=True),
    sa.Column('signuprules', sa.JSON(), nullable=True),
    sa.Column('sticky', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['department'], ['department.id'], ),
    sa.ForeignKeyConstraint(['event'], ['event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('schedule_event',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('starttime', sa.DateTime(), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('schedule', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['schedule'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_role_association',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job', sa.Integer(), nullable=True),
    sa.Column('role', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job'], ['job.id'], ),
    sa.ForeignKeyConstraint(['role'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_schedule_association',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job', sa.Integer(), nullable=True),
    sa.Column('schedule', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job'], ['job.id'], ),
    sa.ForeignKeyConstraint(['schedule'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_schedule_event_association',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job', sa.Integer(), nullable=True),
    sa.Column('schedule_event', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job'], ['job.id'], ),
    sa.ForeignKeyConstraint(['schedule_event'], ['schedule_event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shift',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job', sa.Integer(), nullable=True),
    sa.Column('schedule', sa.Integer(), nullable=True),
    sa.Column('schedule_event', sa.Integer(), nullable=True),
    sa.Column('starttime', sa.DateTime(), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('slots', sa.Integer(), nullable=True),
    sa.Column('filledslots', sa.Integer(), nullable=True),
    sa.Column('weighting', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['job'], ['job.id'], ),
    sa.ForeignKeyConstraint(['schedule'], ['schedule.id'], ),
    sa.ForeignKeyConstraint(['schedule_event'], ['schedule_event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shift_assignment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('badge', sa.Integer(), nullable=True),
    sa.Column('shift', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['badge'], ['badge.id'], ),
    sa.ForeignKeyConstraint(['shift'], ['shift.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shift_signup',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('badge', sa.Integer(), nullable=True),
    sa.Column('job', sa.Integer(), nullable=True),
    sa.Column('shift', sa.Integer(), nullable=True),
    sa.Column('schedule', sa.Integer(), nullable=True),
    sa.Column('schedule_event', sa.Integer(), nullable=True),
    sa.Column('starttime', sa.DateTime(), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('signuptime', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['badge'], ['badge.id'], ),
    sa.ForeignKeyConstraint(['job'], ['job.id'], ),
    sa.ForeignKeyConstraint(['schedule'], ['schedule.id'], ),
    sa.ForeignKeyConstraint(['schedule_event'], ['schedule_event.id'], ),
    sa.ForeignKeyConstraint(['shift'], ['shift.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.alter_column('badge_type',
               existing_type=sa.INTEGER(),
               nullable=True,
               existing_server_default=sa.text('1'))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=128),
               nullable=True)
        batch_op.alter_column('first_name',
               existing_type=sa.VARCHAR(length=128),
               nullable=True)
        batch_op.alter_column('last_name',
               existing_type=sa.VARCHAR(length=128),
               nullable=True)
        batch_op.alter_column('printed_name',
               existing_type=sa.VARCHAR(length=256),
               nullable=True)
        batch_op.alter_column('search_name',
               existing_type=sa.VARCHAR(length=256),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.alter_column('search_name',
               existing_type=sa.VARCHAR(length=256),
               nullable=False)
        batch_op.alter_column('printed_name',
               existing_type=sa.VARCHAR(length=256),
               nullable=False)
        batch_op.alter_column('last_name',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)
        batch_op.alter_column('first_name',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)
        batch_op.alter_column('badge_type',
               existing_type=sa.INTEGER(),
               nullable=False,
               existing_server_default=sa.text('1'))

    op.drop_table('shift_signup')
    op.drop_table('shift_assignment')
    op.drop_table('shift')
    op.drop_table('job_schedule_event_association')
    op.drop_table('job_schedule_association')
    op.drop_table('job_role_association')
    op.drop_table('schedule_event')
    op.drop_table('job')
    op.drop_table('schedule')
    # ### end Alembic commands ###
