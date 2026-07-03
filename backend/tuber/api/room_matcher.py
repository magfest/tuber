from tuber.models import *
import tuber.config
from types import SimpleNamespace
from sqlalchemy import or_
import multiprocessing
import itertools
import datetime
import time


class AntiRequestException(Exception):
    pass


class MatchingError(Exception):
    pass


class HashNS(SimpleNamespace):
    def __hash__(self):
        return self.id

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return self.id < other.id


unmapped = set()


def score_room(staffers, room_night_weight=100, roommate_weight=5, department_weight=1, other_weight=1, allow_empty=True):
    staffers = set(staffers)
    nights = set().union(*[x.room_nights for x in staffers])
    filled_slots = sum([len(x.room_nights) for x in staffers])
    if allow_empty:
        total_slots = len(nights) * len(staffers)
    else:
        total_slots = len(nights) * 4
    room_night_score = room_night_weight * (filled_slots / total_slots)

    filled_requests = 0
    total_requests = 0
    for staffer in staffers:
        for roommate in staffer.roommates:
            if roommate in staffers:
                filled_requests += 1
            total_requests += 1
        for roommate in staffer.iroommates:
            if roommate in staffers:
                filled_requests += 1
            total_requests += 1
    if total_requests:
        roommate_score = roommate_weight * (filled_requests / total_requests)
    else:
        roommate_score = roommate_weight

    filled_dept_req = 0
    total_dept_req = 0
    for staffer in staffers:
        if staffer.prefer_dept:
            total_dept_req += len(staffers) - 1
            for roommate in staffers.difference(set([staffer])):
                if staffer.preferred_dept in roommate.departments:
                    filled_dept_req += 1
    if total_dept_req:
        dept_score = department_weight * (filled_dept_req / total_dept_req)
    else:
        dept_score = department_weight

    genders = set()
    for staffer in staffers:
        if staffer.preferred_gender:
            gender = staffer.preferred_gender.lower().strip()
            if not gender in tuber.config.gender_map:
                print(f"WARNING: Unmapped gender preference: {gender}")
                unmapped.add(gender)
                genders.add(None)
            else:
                genders.add(tuber.config.gender_map[gender])
        else:
            gender = None
    filled_prefs = 0
    total_prefs = 0
    for staffer in staffers:
        if staffer.prefer_single_gender:
            total_prefs += 1
            if len(genders) <= 1:
                filled_prefs += 1
    if total_prefs:
        other_score = other_weight * (filled_prefs / total_prefs)
    else:
        other_score = other_weight

    for staffer in staffers:
        if staffer.antiroommates.intersection(staffers):
            raise AntiRequestException(
                f"{str(staffer)} anti-requested {', '.join([str(x) for x in staffer.antiroommates.intersection(staffers)])}")

    #print(f"Scores: {room_night_score} {roommate_score} {dept_score} {filled_dept_req} {total_dept_req} {', '.join([x.name for x in staffers])}")
    return room_night_score, roommate_score, dept_score, other_score


def get_roommates(staffer, matched, visited=None):
    if not visited:
        visited = set()
    roommates = staffer.roommates.intersection(staffer.iroommates)
    roommates.add(staffer)
    visited.add(staffer)
    for roommate in set(roommates):
        if not roommate in visited:
            roommates.update(get_roommates(roommate, matched, visited))
    return roommates.difference(matched)


def match_perfect(staffers, matched, n):
    rooms = []

    for staffer in staffers:
        if staffer in matched:
            continue
        roommates = get_roommates(staffer, matched)

        best = None
        best_score = 0
        for perm in itertools.combinations(roommates, n):
            try:
                score = sum(score_room(perm))
            except AntiRequestException:
                print(f"Found antirequest in room")
                print(perm)
                continue
            if score > best_score:
                best_score = score
                best = set(perm)
        if best:
            if best.intersection(matched):
                print("Created new staffer", best, matched)
            matched.update(best)
            rooms.append(best)
    return rooms


def combine_rooms(rooms):
    rooms = list(rooms)
    lengths = {4: 0, 3: 0, 2: 0, 1: 0}
    for i in rooms:
        lengths[len(i)] += 1
    print(lengths)

    combined = []
    for room in rooms:
        if len(room) == 4:
            combined.append(room)
    for i in combined:
        rooms.remove(i)

    scores = {}

    while rooms:
        best = None
        best_score = 0
        for perm in itertools.combinations(rooms, 2):
            try:
                a, b = perm
                if len(a) + len(b) > 4:
                    continue
                ordered = list(a.union(b))
                ordered.sort()
                ordered = tuple(ordered)
                if ordered in scores:
                    score = scores[ordered]
                else:
                    score = sum(score_room(ordered, allow_empty=False))
                    scores[ordered] = score
            except AntiRequestException:
                continue
            if score > best_score:
                best_score = score
                best = perm
        if best:
            combined.append(set.union(*best))
            rooms.remove(best[0])
            rooms.remove(best[1])
        else:
            for i in rooms:
                combined.append(i)
            rooms = []
    lengths = {4: 0, 3: 0, 2: 0, 1: 0}
    for i in combined:
        lengths[len(i)] += 1
    print(lengths)
    return combined


def load_staffer_pool(db, event, hotel_block, badge_ids=None,
                      exclude_assigned=True, exclude_completed_room=False):
    """Load matcher staffer objects for a block.

    exclude_assigned: only people with no room night assignments at all (the
        classic matching pool).
    exclude_completed_room: allow people with assignments unless any of them
        is in a room marked completed (the roommate-suggestion pool).
    badge_ids: restrict to specific badges (e.g. a room's current occupants),
        ignoring the assignment filters.
    """
    room_nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).all()
    query = db.query(HotelRoomRequest, Badge).join(
        Badge, Badge.id == HotelRoomRequest.badge).filter(
        HotelRoomRequest.hotel_block == hotel_block,
        or_(HotelRoomRequest.declined == None, HotelRoomRequest.declined == False))
    if badge_ids is not None:
        query = query.filter(HotelRoomRequest.badge.in_(badge_ids))
    elif exclude_assigned:
        query = query.filter(~HotelRoomRequest.room_night_assignments.any())
    elif exclude_completed_room:
        completed_badges = db.query(RoomNightAssignment.badge).join(
            HotelRoom, RoomNightAssignment.hotel_room == HotelRoom.id).filter(
            HotelRoom.event == event, HotelRoom.completed == True).subquery()
        query = query.filter(~HotelRoomRequest.badge.in_(completed_badges.select()))
    requests = query.all()
    staffers = []
    for request, badge in requests:
        staffer = HashNS()

        #approved = set()
        #for approval in request.room_night_approvals:
        #    if approval.approved:
        #        approved.add(approval.room_night)

        requested = set()
        for night_request in request.room_night_requests:
            if night_request.requested:
                requested.add(night_request.room_night)

        assigned = set()
        for room_night in room_nights:
            if room_night.id in requested:
                #if not room_night.restricted or room_night.id in approved:
                    assigned.add(room_night.id)

        if assigned:
            staffer.room_nights = assigned
            staffer.id = badge.id
            staffer.request = request
            staffer.roommates = set()
            staffer.iroommates = set()  # incoming roommate requests
            staffer.antiroommates = set()
            staffer.iantiroommates = set()  # incoming antiroommate requests
            staffer.departments = badge.departments
            staffer.prefer_dept = request.prefer_department
            staffer.preferred_dept = request.preferred_department or (
                badge.departments[0] if badge.departments else None)
            staffer.hotel_block = request.hotel_block
            staffer.name = badge.public_name
            staffer.preferred_gender = request.preferred_gender
            staffer.prefer_single_gender = request.prefer_single_gender
            staffers.append(staffer)

    stafferlookup = {x.id: x for x in staffers}
    for staffer in staffers:
        for roommate in staffer.request.roommate_requests:
            if roommate.id in stafferlookup:
                rm_badge = stafferlookup[roommate.id]
                staffer.roommates.add(rm_badge)
                rm_badge.iroommates.add(staffer)
        for antiroommate in staffer.request.roommate_anti_requests:
            if antiroommate.id in stafferlookup:
                rm_badge = stafferlookup[antiroommate.id]
                staffer.antiroommates.add(rm_badge)
                rm_badge.iantiroommates.add(staffer)
    return staffers


def load_staffers(db, event, hotel_block):
    return load_staffer_pool(db, event, hotel_block)


def clear_hotel_block(db, event, hotel_block, suggested_only=False):
    """Delete matcher-created rooms in a block. With suggested_only (the
       default behavior of the rematch/clear endpoints) hand-built rooms are
       left alone; only unaccepted suggestions are removed."""
    rooms = db.query(HotelRoom).filter(HotelRoom.hotel_block == hotel_block,
                                       HotelRoom.completed == False, HotelRoom.locked == False)
    if suggested_only:
        rooms = rooms.filter(HotelRoom.suggested == True)
    for room in rooms.all():
        db.delete(room)
    db.commit()


def rematch_hotel_block(db, event, hotel_block):
    clear_hotel_block(db, event, hotel_block, suggested_only=True)
    return match_block(db, event, hotel_block)


def match_block(db, event, hotel_block):
    """Run the matcher over everyone in the block who has no assignments yet,
       creating persisted suggested rooms for review. Returns created room ids."""
    start = time.perf_counter()
    staffers = load_staffer_pool(db, event, hotel_block)
    if not staffers:
        return []
    print(f"Load time: {time.perf_counter() - start}")

    start = time.perf_counter()
    print(f"Starting with {len(staffers)} Staffers")
    matched = set()
    all_rooms = []
    for n in range(4, 1, -1):
        rooms = match_perfect(set(staffers), matched, n)
        all_rooms.extend(rooms)
        matched = matched.union(*rooms)
        print(f"Matched rooms of at least {n}")
        print(
            f"Got {len(rooms)} rooms and {len(matched)} total cumulative matches")
    print(f"Perfect Match time: {time.perf_counter() - start}")

    start = time.perf_counter()
    remaining = set(staffers).difference(matched)
    print(f"Giving the remaining {len(remaining)} staffers their own rooms")
    all_rooms.extend([set([x]) for x in remaining])
    matched = set.union(*all_rooms)
    print(
        f"Now have {sum(map(len, all_rooms))} Staffers Matched of {len(staffers)} into {len(all_rooms)} rooms")
    assert len(matched) == len(staffers)
    print(f"Single Match time: {time.perf_counter() - start}")

    start = time.perf_counter()
    start_len = len(all_rooms)
    all_rooms = combine_rooms(all_rooms)
    print(f"Combined {start_len} rooms into {len(all_rooms)}")
    print(f"Combine Round 1 time: {time.perf_counter() - start}")

    start = time.perf_counter()
    all_rooms = combine_rooms(all_rooms)
    print(f"Combined {start_len} rooms into {len(all_rooms)}")
    print(f"Combine Round 2 time: {time.perf_counter() - start}")

    hotels = []
    for idx, room in enumerate(all_rooms):
        hotel_room = HotelRoom(
            event=event, hotel_block=hotel_block,
            name=f"Suggested Room {idx + 1}", suggested=True)
        db.add(hotel_room)
        hotels.append((room, hotel_room))
    db.flush()

    for room, hotel_room in hotels:
        for roommate in room:
            for room_night in roommate.room_nights:
                assoc = RoomNightAssignment(
                    event=event, badge=roommate.id, hotel_room=hotel_room.id, room_night=room_night)
                db.add(assoc)
            db.add(roommate.request)
    db.commit()
    print(unmapped)
    return [hotel_room.id for _, hotel_room in hotels]


def suggest_roommates(db, event, room, limit=10):
    """Rank the best additions to a room using the matcher's scoring.

    Candidates are people in the room's block who are not in any completed
    room (people sitting in incomplete or suggested rooms are fair game and
    would be moved). Anti-request conflicts are skipped outright.
    """
    occupant_ids = {x.id for x in room.roommates}
    pool = load_staffer_pool(db, event, room.hotel_block,
                             exclude_assigned=False, exclude_completed_room=True)
    # Occupants may not appear in the pool (e.g. declined since placement);
    # load them explicitly so scoring sees the full room.
    pool_ids = {x.id for x in pool}
    missing_occupants = occupant_ids - pool_ids
    if missing_occupants:
        pool.extend(load_staffer_pool(db, event, room.hotel_block,
                                      badge_ids=missing_occupants))
    occupants = {x for x in pool if x.id in occupant_ids}
    candidates = [x for x in pool if x.id not in occupant_ids]

    room_night_ids = {x.room_night for x in room.room_night_assignments}
    current_rooms = {}
    if candidates:
        for rna in db.query(RoomNightAssignment).filter(
                RoomNightAssignment.badge.in_([x.id for x in candidates]),
                RoomNightAssignment.hotel_room != None).all():
            current_rooms[rna.badge] = rna.hotel_room

    scored = []
    for candidate in candidates:
        try:
            parts = score_room(occupants | {candidate})
        except AntiRequestException:
            continue
        scored.append((sum(parts), parts, candidate))
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for total, parts, candidate in scored[:limit]:
        results.append({
            "badge": candidate.id,
            "name": candidate.name,
            "score": round(total, 2),
            "score_parts": {
                "room_night": round(parts[0], 2),
                "roommate": round(parts[1], 2),
                "department": round(parts[2], 2),
                "other": round(parts[3], 2),
            },
            "nights": sorted(candidate.room_nights),
            "missing_in_room": sorted(room_night_ids - candidate.room_nights),
            "current_room": current_rooms.get(candidate.id),
        })
    return results
