from collections import Counter, defaultdict
from flask import request, jsonify
from sqlalchemy import or_
from tuber import app
from tuber.database import db
from tuber.models import *
from tuber.permissions import *
from .room_matcher import load_staffer_pool, night_match, normalize_gender, get_roommates
import math
import tuber.config

ROOM_SIZE = 4


def _night_stats(staffers, nights):
    """How much the requested nights line up. The floor packs every night
       independently (the fewest room-nights possible); the exact-pattern cost
       is what it takes if rooms only ever hold identical nights. The gap
       between them is how much the matcher must mix nights to save rooms."""
    per_night = Counter()
    patterns = Counter()
    for staffer in staffers:
        per_night.update(staffer.room_nights)
        patterns[frozenset(staffer.room_nights)] += 1
    floor = sum(math.ceil(count / ROOM_SIZE) for count in per_night.values())
    exact = sum(math.ceil(count / ROOM_SIZE) * len(pattern) for pattern, count in patterns.items())
    person_nights = sum(per_night.values())
    order = {night.id: idx for idx, night in enumerate(nights)}
    top = patterns.most_common()
    return {
        "people": len(staffers),
        "person_nights": person_nights,
        "average_nights": round(person_nights / len(staffers), 1) if staffers else 0,
        "per_night": [{"id": night.id, "name": night.name, "people": per_night[night.id],
                       "rooms": math.ceil(per_night[night.id] / ROOM_SIZE)} for night in nights],
        "room_night_floor": floor,
        "exact_pattern_room_nights": exact,
        "floor_occupancy": round(person_nights / (floor * ROOM_SIZE) * 100, 1) if floor else 0,
        "distinct_patterns": len(patterns),
        "unique_patterns": len([x for x in patterns.values() if x == 1]),
        "top3_share": round(sum(count for _, count in top[:3]) / len(staffers) * 100, 1) if staffers else 0,
        # People left over after filling whole rooms with an identical pattern.
        "pattern_leftovers": sum(count % ROOM_SIZE for count in patterns.values()),
        "top_patterns": [{"nights": sorted(pattern, key=lambda x: order.get(x, 0)), "people": count}
                         for pattern, count in top[:5]],
    }


def _roommate_stats(staffers, event, hotel_block):
    """Roommate requests: mutual vs one-way, who can't be honored and why,
       request groups that won't fit a room, and night agreement within pairs."""
    pool = {x.id: x for x in staffers}
    requesters = [x for x in staffers if x.request.roommate_requests]
    total = mutual = one_way = 0
    unplaceable = Counter()
    others = {}
    wanted = {r.id for x in staffers for r in x.request.roommate_requests if r.id not in pool}
    if wanted:
        for req in db.query(HotelRoomRequest).filter(HotelRoomRequest.event == event,
                                                     HotelRoomRequest.badge.in_(wanted)).all():
            others[req.badge] = req
    for staffer in staffers:
        for roommate in staffer.request.roommate_requests:
            total += 1
            if roommate.id in pool:
                if staffer in pool[roommate.id].roommates:
                    mutual += 1
                else:
                    one_way += 1
                continue
            other = others.get(roommate.id)
            if not other:
                unplaceable["no_request"] += 1
            elif other.declined:
                unplaceable["declined"] += 1
            elif other.hotel_block != hotel_block:
                unplaceable["other_block"] += 1
            else:
                unplaceable["no_eligible_nights"] += 1

    # Mutual pairs counted once, with how well their nights agree.
    pairs = {tuple(sorted((a.id, b.id))) for a in staffers for b in a.roommates if a in b.roommates}
    identical = len([1 for a, b in pairs if pool[a].room_nights == pool[b].room_nights])
    match = [night_match([pool[a], pool[b]]) for a, b in pairs]

    seen = set()
    group_sizes = Counter()
    for staffer in staffers:
        if staffer in seen:
            continue
        group = get_roommates(staffer, set())
        seen.update(group)
        if len(group) > 1:
            group_sizes[len(group)] += 1

    conflicts = len([1 for a in staffers for b in a.roommates if a in b.antiroommates])
    return {
        "requesters": len(requesters),
        "requests": total,
        "mutual_pairs": len(pairs),
        "one_way": one_way,
        "unplaceable": dict(unplaceable),
        "pairs_identical_nights": identical,
        "pairs_night_match": round(sum(match) / len(match) * 100, 1) if match else None,
        "group_sizes": {str(k): v for k, v in sorted(group_sizes.items())},
        "oversized_groups": sum(v for k, v in group_sizes.items() if k > ROOM_SIZE),
        "anti_requests": sum(len(x.antiroommates) for x in staffers),
        "conflicts": conflicts,
        "prefer_department": len([x for x in staffers if x.prefer_dept]),
    }


def _gender_stats(staffers):
    """Who asked for single-gender rooms, and how many people of the same
       stated gender they could share with. People who left gender blank can
       only share with single-gender requesters who also left it blank."""
    buckets = defaultdict(lambda: {"requesters": 0, "people": 0})
    for staffer in staffers:
        gender = normalize_gender(staffer.preferred_gender)
        if gender is None:
            continue
        buckets[gender]["people"] += 1
        if staffer.prefer_single_gender:
            buckets[gender]["requesters"] += 1
    mapped = set(tuber.config.gender_map.values())
    requesters = [x for x in staffers if x.prefer_single_gender]
    return {
        "requesters": len(requesters),
        "requesters_blank": len([x for x in requesters if not normalize_gender(x.preferred_gender)]),
        "blank": len([x for x in staffers if not normalize_gender(x.preferred_gender)]),
        "buckets": sorted([{"gender": gender, "mapped": gender in mapped, **counts}
                           for gender, counts in buckets.items() if counts["requesters"]],
                          key=lambda x: -x["requesters"]),
        "unmapped_answers": sorted(gender for gender in buckets if gender not in mapped),
    }


def _booked_room_nights(event, hotel_block):
    rows = db.query(RoomNightAssignment.hotel_room, RoomNightAssignment.room_night).join(
        HotelRoom, HotelRoom.id == RoomNightAssignment.hotel_room).filter(
        HotelRoom.event == event, HotelRoom.hotel_block == hotel_block).distinct().all()
    return len(rows)


@app.route("/api/event/<int:event>/hotel/match_stats", methods=["GET"])
def hotel_match_stats(event):
    """Per block: how well the open requests could fit into rooms, from the
       nights, roommate and gender answers alone (not the current rooms)."""
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    approved_only = request.args.get("nights") != "requested"
    nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).order_by(HotelRoomNight.date).all()
    blocks = db.query(HotelRoomBlock).filter(
        HotelRoomBlock.event == event).order_by(HotelRoomBlock.name).all()
    results = []
    for block in blocks:
        staffers = load_staffer_pool(db, event, block.id, exclude_assigned=False,
                                     approved_only=approved_only)
        requested = len(load_staffer_pool(db, event, block.id, exclude_assigned=False,
                                          approved_only=False))
        open_requests = db.query(HotelRoomRequest).filter(
            HotelRoomRequest.event == event, HotelRoomRequest.hotel_block == block.id,
            or_(HotelRoomRequest.declined == None, HotelRoomRequest.declined == False)).count()
        results.append({
            "id": block.id,
            "name": block.name,
            "open_requests": open_requests,
            "no_nights_requested": open_requests - requested,
            "no_eligible_nights": requested - len(staffers),
            "booked_room_nights": _booked_room_nights(event, block.id),
            "nights": _night_stats(staffers, nights),
            "roommates": _roommate_stats(staffers, event, block.id),
            "gender": _gender_stats(staffers),
        })
    return jsonify(results)
