"""Single source of truth for room night eligibility.

A room night's `restriction_mode` decides how a badge becomes approved for it:
    none         - approved for everyone
    shift_window - a shift overlapping [shift_starttime, shift_endtime]
    shift_hours  - total assigned shift hours >= shift_hours_required
    manual       - a manual approval only
A manual approval (RoomNightApproval.approved == True, from a department head
or an event-level admin) satisfies any mode.

These helpers compute approvals for many badges in a constant number of
queries; list endpoints should prefer them over the per-badge
Badge.approved_hotel_nights property.
"""
from collections import defaultdict

from sqlalchemy import func

from tuber.models import (HotelRoomNight, RoomNightApproval, Shift,
                          ShiftAssignment)


def shift_hours_totals(db, event, badge_ids=None):
    """Total assigned shift hours per badge -> {badge_id: float hours}."""
    query = db.query(ShiftAssignment.badge, func.sum(Shift.duration)).join(
        Shift, ShiftAssignment.shift == Shift.id).filter(
        Shift.event == event).group_by(ShiftAssignment.badge)
    if badge_ids is not None:
        query = query.filter(ShiftAssignment.badge.in_(badge_ids))
    return {badge: (seconds or 0) / 3600 for badge, seconds in query.all()}


def shift_satisfied_night_ids(db, event, badge_ids=None, nights=None):
    """Nights whose shift-based criteria a badge meets on its own merits
       (shift_window overlap or shift_hours total) -> {badge_id: set(night_id)}.
       Excludes manual approvals and unrestricted nights."""
    if nights is None:
        nights = db.query(HotelRoomNight).filter(
            HotelRoomNight.event == event).all()
    satisfied = defaultdict(set)

    window_nights = [x for x in nights if x.restriction_mode == 'shift_window'
                     and x.shift_starttime and x.shift_endtime]
    if window_nights:
        query = db.query(ShiftAssignment.badge, HotelRoomNight.id).join(
            Shift, ShiftAssignment.shift == Shift.id).join(
            HotelRoomNight, HotelRoomNight.event == Shift.event).filter(
            Shift.event == event,
            HotelRoomNight.id.in_([x.id for x in window_nights]),
            Shift.starttime < HotelRoomNight.shift_endtime,
            (Shift.starttime + func.make_interval(0, 0, 0, 0, 0, 0, Shift.duration))
            > HotelRoomNight.shift_starttime).distinct()
        if badge_ids is not None:
            query = query.filter(ShiftAssignment.badge.in_(badge_ids))
        for badge, night in query.all():
            satisfied[badge].add(night)

    hours_nights = [x for x in nights if x.restriction_mode == 'shift_hours'
                    and x.shift_hours_required]
    if hours_nights:
        for badge, hours in shift_hours_totals(db, event, badge_ids).items():
            for night in hours_nights:
                if hours >= night.shift_hours_required:
                    satisfied[badge].add(night.id)

    return satisfied


def manual_approved_night_ids(db, event, badge_ids=None):
    """Manually approved nights per badge -> {badge_id: set(night_id)}."""
    query = db.query(RoomNightApproval.badge, RoomNightApproval.room_night).filter(
        RoomNightApproval.event == event, RoomNightApproval.approved == True)
    if badge_ids is not None:
        query = query.filter(RoomNightApproval.badge.in_(badge_ids))
    approved = defaultdict(set)
    for badge, night in query.all():
        approved[badge].add(night)
    return approved


def approved_night_ids(db, event, badge_ids=None):
    """All approved night ids per badge -> defaultdict {badge_id: set(night_id)}.

    Union of: unrestricted nights (everyone), shift-based satisfaction, and
    manual approvals (which satisfy any mode). The returned defaultdict yields
    the unrestricted baseline for badges with no other rows.
    """
    nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).all()
    unrestricted = {x.id for x in nights if x.restriction_mode == 'none'}
    approved = defaultdict(lambda: set(unrestricted))
    if badge_ids is not None:
        for badge in badge_ids:
            approved[badge]  # materialize the unrestricted baseline
    for badge, night_ids in shift_satisfied_night_ids(
            db, event, badge_ids, nights=nights).items():
        approved[badge].update(night_ids)
    for badge, night_ids in manual_approved_night_ids(
            db, event, badge_ids).items():
        approved[badge].update(night_ids)
    return approved
