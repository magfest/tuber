"""Setting nullable FKs to SET NULL ondelete

Revision ID: 7e310668394d
Revises: cd6926818967
Create Date: 2022-11-20 16:16:20.924344

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e310668394d'
down_revision = 'cd6926818967'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('background_job', schema=None) as batch_op:
        batch_op.drop_constraint('background_job_session_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'session', ['session'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.drop_constraint('badge_user_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('badge_badge_type_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'user', ['user'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'badge_type', ['badge_type'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('email', schema=None) as batch_op:
        batch_op.drop_constraint('email_source_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'email_source', ['source'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('email_receipt', schema=None) as batch_op:
        batch_op.drop_constraint('email_receipt_trigger_fkey', type_='foreignkey')
        batch_op.drop_constraint('email_receipt_source_fkey', type_='foreignkey')
        batch_op.drop_constraint('email_receipt_badge_fkey', type_='foreignkey')
        batch_op.drop_constraint('email_receipt_email_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'email', ['email'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'email_trigger', ['trigger'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'email_source', ['source'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'badge', ['badge'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_room_hotel_block_fkey', type_='foreignkey')
        batch_op.drop_constraint('hotel_room_hotel_location_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'hotel_room_block', ['hotel_block'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'hotel_location', ['hotel_location'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('hotel_room_request', schema=None) as batch_op:
        batch_op.drop_constraint('hotel_room_request_hotel_block_fkey', type_='foreignkey')
        batch_op.drop_constraint('hotel_room_request_preferred_department_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'department', ['preferred_department'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'hotel_room_block', ['hotel_block'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('shift', schema=None) as batch_op:
        batch_op.drop_constraint('shift_schedule_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_schedule_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'schedule', ['schedule'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'schedule_event', ['schedule_event'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('shift_signup', schema=None) as batch_op:
        batch_op.drop_constraint('shift_signup_job_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_signup_schedule_event_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_signup_shift_fkey', type_='foreignkey')
        batch_op.drop_constraint('shift_signup_schedule_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'schedule_event', ['schedule_event'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'schedule', ['schedule'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'job', ['job'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'shift', ['shift'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('user_default_event_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'event', ['default_event'], ['id'], ondelete='SET NULL')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('user_default_event_fkey', 'event', ['default_event'], ['id'])

    with op.batch_alter_table('shift_signup', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('shift_signup_schedule_fkey', 'schedule', ['schedule'], ['id'])
        batch_op.create_foreign_key('shift_signup_shift_fkey', 'shift', ['shift'], ['id'])
        batch_op.create_foreign_key('shift_signup_schedule_event_fkey', 'schedule_event', ['schedule_event'], ['id'])
        batch_op.create_foreign_key('shift_signup_job_fkey', 'job', ['job'], ['id'])

    with op.batch_alter_table('shift', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('shift_schedule_event_fkey', 'schedule_event', ['schedule_event'], ['id'])
        batch_op.create_foreign_key('shift_schedule_fkey', 'schedule', ['schedule'], ['id'])

    with op.batch_alter_table('hotel_room_request', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_room_request_preferred_department_fkey', 'department', ['preferred_department'], ['id'])
        batch_op.create_foreign_key('hotel_room_request_hotel_block_fkey', 'hotel_room_block', ['hotel_block'], ['id'])

    with op.batch_alter_table('hotel_room', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('hotel_room_hotel_location_fkey', 'hotel_location', ['hotel_location'], ['id'])
        batch_op.create_foreign_key('hotel_room_hotel_block_fkey', 'hotel_room_block', ['hotel_block'], ['id'])

    with op.batch_alter_table('email_receipt', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('email_receipt_email_fkey', 'email', ['email'], ['id'])
        batch_op.create_foreign_key('email_receipt_badge_fkey', 'badge', ['badge'], ['id'])
        batch_op.create_foreign_key('email_receipt_source_fkey', 'email_source', ['source'], ['id'])
        batch_op.create_foreign_key('email_receipt_trigger_fkey', 'email_trigger', ['trigger'], ['id'])

    with op.batch_alter_table('email', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('email_source_fkey', 'email_source', ['source'], ['id'])

    with op.batch_alter_table('badge', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('badge_badge_type_fkey', 'badge_type', ['badge_type'], ['id'])
        batch_op.create_foreign_key('badge_user_id_fkey', 'user', ['user'], ['id'])

    with op.batch_alter_table('background_job', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('background_job_session_fkey', 'session', ['session'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###
