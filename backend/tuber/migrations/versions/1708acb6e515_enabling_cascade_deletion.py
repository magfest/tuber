"""Enabling cascade deletion

Revision ID: 1708acb6e515
Revises: b40cd963a916
Create Date: 2021-11-12 03:00:11.610978

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1708acb6e515'
down_revision = 'b40cd963a916'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_constraint('api_key_user_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'user', ['user'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('background_job', schema=None) as batch_op:
        batch_op.drop_constraint('background_job_session_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'session', ['session'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.drop_constraint('badge_event_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('department', schema=None) as batch_op:
        batch_op.drop_constraint('department_event_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('department_grant', schema=None) as batch_op:
        batch_op.drop_constraint('department_grant_role_fkey', type_='foreignkey')
        batch_op.drop_constraint('department_grant_department_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'department_role', ['role'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'department', ['department'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('department_permission', schema=None) as batch_op:
        batch_op.drop_constraint('department_permission_role_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'department_role', ['role'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('email', schema=None) as batch_op:
        batch_op.drop_constraint('email_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('email_receipt', schema=None) as batch_op:
        batch_op.add_column(sa.Column('event', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('email_source', schema=None) as batch_op:
        batch_op.drop_constraint('email_source_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('email_trigger', schema=None) as batch_op:
        batch_op.add_column(sa.Column('event', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('grant', schema=None) as batch_op:
        batch_op.drop_constraint('grant_user_fkey', type_='foreignkey')
        batch_op.drop_constraint('grant_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('grant_role_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'role', ['role'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'user', ['user'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_anti_roommate_request', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_anti_roommate_request_requested_fkey', type_='foreignkey')
        batch_op.drop_constraint('hotel_anti_roommate_request_requester_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'badge', ['requester'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'badge', ['requested'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_room_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_room_block', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_room_block_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_room_night', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_room_night_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_room_request', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_room_request_badge_fkey', type_='foreignkey')
        batch_op.drop_constraint('hotel_room_request_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_roommate_request', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_roommate_request_requested_fkey', type_='foreignkey')
        batch_op.drop_constraint('hotel_roommate_request_requester_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'badge', ['requester'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'badge', ['requested'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('job', schema=None) as batch_op:
        batch_op.drop_constraint('job_department_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'department', ['department'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('job_role_association', schema=None) as batch_op:
        batch_op.drop_constraint('job_role_association_job_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_role_association_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_role_association_role_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'job', ['job'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'department_role', ['role'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('job_schedule_association', schema=None) as batch_op:
        batch_op.drop_constraint('job_schedule_association_job_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_schedule_association_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_schedule_association_schedule_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'job', ['job'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'schedule', ['schedule'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('job_schedule_event_association', schema=None) as batch_op:
        batch_op.drop_constraint('job_schedule_event_association_schedule_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_schedule_event_association_job_fkey', type_='foreignkey')
        batch_op.drop_constraint('job_schedule_event_association_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'job', ['job'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'schedule_event', ['schedule_event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('permission', schema=None) as batch_op:
        batch_op.drop_constraint('permission_role_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'role', ['role'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('room_night_approval', schema=None) as batch_op:
        batch_op.drop_constraint('room_night_approval_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_approval_hotel_room_night_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_approval_department_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_approval_badge_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'hotel_room_night', ['room_night'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'department', ['department'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('room_night_assignment', schema=None) as batch_op:
        batch_op.drop_constraint('room_night_assignment_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_assignment_hotel_room_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_assignment_room_night_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_assignment_badge_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'hotel_room_night', ['room_night'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'hotel_room', ['hotel_room'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('room_night_request', schema=None) as batch_op:
        batch_op.drop_constraint('badge_to_room_night_room_night_fkey', type_='foreignkey')
        batch_op.drop_constraint('room_night_request_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('badge_to_room_night_badge_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'hotel_room_night', ['room_night'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('schedule', schema=None) as batch_op:
        batch_op.drop_constraint('schedule_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('schedule_event', schema=None) as batch_op:
        batch_op.drop_constraint('schedule_event_schedule_fkey', type_='foreignkey')
        batch_op.drop_constraint('schedule_event_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'schedule', ['schedule'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('session', schema=None) as batch_op:
        batch_op.drop_constraint('session_user_fkey', type_='foreignkey')
        batch_op.drop_constraint('session_badge_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'user', ['user'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('shift', schema=None) as batch_op:
        batch_op.drop_constraint('shift_job_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'job', ['job'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('shift_assignment', schema=None) as batch_op:
        batch_op.drop_constraint('shift_assignment_shift_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_assignment_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_assignment_badge_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'shift', ['shift'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('shift_signup', schema=None) as batch_op:
        batch_op.drop_constraint('shift_signup_badge_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_signup_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['event'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('shift_signup', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('shift_signup_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('shift_signup_badge_fkey', 'badge', ['badge'], ['id'])

    with op.batch_alter_table('shift_assignment', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('shift_assignment_badge_fkey', 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key('shift_assignment_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('shift_assignment_shift_fkey', 'shift', ['shift'], ['id'])

    with op.batch_alter_table('shift', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('shift_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('shift_job_fkey', 'job', ['job'], ['id'])

    with op.batch_alter_table('session', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('session_badge_fkey', 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key('session_user_fkey', 'user', ['user'], ['id'])

    with op.batch_alter_table('schedule_event', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('schedule_event_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('schedule_event_schedule_fkey', 'schedule', ['schedule'], ['id'])

    with op.batch_alter_table('schedule', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('schedule_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('room_night_request', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('badge_to_room_night_badge_fkey', 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key('room_night_request_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('badge_to_room_night_room_night_fkey', 'hotel_room_night', ['room_night'], ['id'])

    with op.batch_alter_table('room_night_assignment', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('room_night_assignment_badge_fkey', 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key('room_night_assignment_room_night_fkey', 'hotel_room_night', ['room_night'], ['id'])
        batch_op.create_foreign_key('room_night_assignment_hotel_room_fkey', 'hotel_room', ['hotel_room'], ['id'])
        batch_op.create_foreign_key('room_night_assignment_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('room_night_approval', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('room_night_approval_badge_fkey', 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key('room_night_approval_department_fkey', 'department', ['department'], ['id'])
        batch_op.create_foreign_key('room_night_approval_hotel_room_night_fkey', 'hotel_room_night', ['room_night'], ['id'])
        batch_op.create_foreign_key('room_night_approval_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('permission', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('permission_role_fkey', 'role', ['role'], ['id'])

    with op.batch_alter_table('job_schedule_event_association', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('job_schedule_event_association_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('job_schedule_event_association_job_fkey', 'job', ['job'], ['id'])
        batch_op.create_foreign_key('job_schedule_event_association_schedule_event_fkey', 'schedule_event', ['schedule_event'], ['id'])

    with op.batch_alter_table('job_schedule_association', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('job_schedule_association_schedule_fkey', 'schedule', ['schedule'], ['id'])
        batch_op.create_foreign_key('job_schedule_association_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('job_schedule_association_job_fkey', 'job', ['job'], ['id'])

    with op.batch_alter_table('job_role_association', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('job_role_association_role_fkey', 'department_role', ['role'], ['id'])
        batch_op.create_foreign_key('job_role_association_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('job_role_association_job_fkey', 'job', ['job'], ['id'])

    with op.batch_alter_table('job', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('job_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('job_department_fkey', 'department', ['department'], ['id'])

    with op.batch_alter_table('hotel_roommate_request', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_roommate_request_requester_fkey', 'badge', ['requester'], ['id'])
        batch_op.create_foreign_key('hotel_roommate_request_requested_fkey', 'badge', ['requested'], ['id'])

    with op.batch_alter_table('hotel_room_request', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_room_request_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('hotel_room_request_badge_fkey', 'badge', ['badge'], ['id'])

    with op.batch_alter_table('hotel_room_night', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_room_night_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('hotel_room_block', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_room_block_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_room_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('hotel_anti_roommate_request', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_anti_roommate_request_requester_fkey', 'badge', ['requester'], ['id'])
        batch_op.create_foreign_key('hotel_anti_roommate_request_requested_fkey', 'badge', ['requested'], ['id'])

    with op.batch_alter_table('grant', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('grant_role_fkey', 'role', ['role'], ['id'])
        batch_op.create_foreign_key('grant_event_fkey', 'event', ['event'], ['id'])
        batch_op.create_foreign_key('grant_user_fkey', 'user', ['user'], ['id'])

    with op.batch_alter_table('email_trigger', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('event')

    with op.batch_alter_table('email_source', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('email_source_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('email_receipt', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('event')

    with op.batch_alter_table('email', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('email_event_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('department_permission', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('department_permission_role_fkey', 'department_role', ['role'], ['id'])

    with op.batch_alter_table('department_grant', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('department_grant_department_fkey', 'department', ['department'], ['id'])
        batch_op.create_foreign_key('department_grant_role_fkey', 'department_role', ['role'], ['id'])

    with op.batch_alter_table('department', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('department_event_id_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('badge_event_id_fkey', 'event', ['event'], ['id'])

    with op.batch_alter_table('background_job', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('background_job_session_fkey', 'session', ['session'], ['id'])

    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('api_key_user_fkey', 'user', ['user'], ['id'])

    # ### end Alembic commands ###