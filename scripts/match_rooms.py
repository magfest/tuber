from secrets import TUBER_URL, TUBER_APIKEY, TUBER_EVENT
from types import SimpleNamespace
import itertools
import datetime
import uber_api
import requests
import json
import sys
import os

headers = {
    "X-Auth-Token": TUBER_APIKEY
}

BASE_URL = f'{TUBER_URL}/api/event/{TUBER_EVENT}'

class AntiRequestException(Exception): pass

class MatchingError(Exception): pass

def get(url, as_dict=False, refresh=False):
    path = os.path.join("cache", url.replace("/", "_")+".json")
    if os.path.isfile(path) and not refresh:
        with open(path, "r") as FILE:
            data = json.loads(FILE.read())
    else:
        data = requests.get(url, headers=headers).json()
        with open(path, "w") as FILE:
            FILE.write(json.dumps(data))
    if as_dict:
        return {x['id']: x for x in data}
    return data


room_requests = get(f'{BASE_URL}/hotel_room_request?full=true', as_dict=True)
badges = get(f'{BASE_URL}/badge?full=true')
badgelookup = {x['id']: x for x in badges}
night_requests = get(f'{BASE_URL}/room_night_request', as_dict=True)
departments = get(f'{BASE_URL}/department')
room_nights = get(f'{BASE_URL}/hotel_room_night', as_dict=True)
hotel_blocks = get(f'{BASE_URL}/hotel_room_block')

approved_nights = {}
for badge in badges:
    approved_nights[badge['id']] = set([room_nights[x]['id'] for x in room_nights if not room_nights[x]['restricted']])

for department in departments:
    night_approvals = get(f'{BASE_URL}/department/{department["id"]}/room_night_approval')
    for approval in night_approvals:
        if approval['approved']:
            approved_nights[approval['badge']].add(approval['room_night'])

room_night_mapping = {}
for night in room_nights.values():
    days = (datetime.datetime.strptime(night['date'], "%Y-%m-%d") - datetime.datetime(1970,1,1)).days
    room_night_mapping[night['id']] = days

start = min(room_night_mapping.values())
room_night_mapping = {k: v-start for k, v in room_night_mapping.items()}

stats = {
    "approved_nights": 0,
    "requested_nights": 0,
    "people": 0,
    "block_counts": {},
    "islands": 0,
    "island_sizes": {}
}

class HashNS(SimpleNamespace):
    def __hash__(self):
        return self.id

    def __repr__(self):
        return self.name

staffers = []
for badge in badges:
    staffer = HashNS()
    requested = set()
    for night_request in badge['room_night_requests']:
        if night_requests[night_request]['requested']:
            requested.add(night_requests[night_request]['room_night'])
    for room_night in requested.intersection(approved_nights[badge['id']]):
        stats['approved_nights'] += 1
    for room_night in requested:
        stats['requested_nights'] += 1

    # TODO: Change this to the intersection of requested and approved once more approvals are in
    if requested:
        staffer.room_nights = [room_night_mapping[x] for x in requested]
        staffer.room_nights.sort()
        staffer.badge = badge
        staffer.id = badge['id']
        staffer.request = room_requests[badge['hotel_room_request'][0]]
        staffer.roommates = set()
        staffer.iroommates = set() # incoming roommate requests
        staffer.antiroommates = set()
        staffer.iantiroommates = set() # incoming antiroommate requests
        staffer.departments = badge['departments']
        staffer.prefer_dept = staffer.request['prefer_department']
        staffer.preferred_dept = staffer.request['preferred_department'] or (badge['departments'][0] if badge['departments'] else None)
        staffer.hotel_block = staffer.request['hotel_block']
        staffer.name = badge['public_name']
        staffers.append(staffer)
        stats['people'] += 1

stafferlookup = {x.badge['id']: x for x in staffers}
for staffer in staffers:
    for roommate in staffer.request['roommate_requests']:
        rm_badge = badgelookup[roommate]
        if room_requests[rm_badge['hotel_room_request'][0]]['hotel_block'] == staffer.request['hotel_block']:
            staffer.roommates.add(stafferlookup[rm_badge['id']])
            stafferlookup[rm_badge['id']].iroommates.add(staffer)
    for antiroommate in staffer.request['roommate_anti_requests']:
        rm_badge = badgelookup[antiroommate]
        if room_requests[rm_badge['hotel_room_request'][0]]['hotel_block'] == staffer.request['hotel_block']:
            staffer.antiroommates.add(stafferlookup[rm_badge['id']])
            stafferlookup[rm_badge['id']].iantiroommates.add(staffer)

def score_room(staffers, room_night_weight=10, roommate_weight=5, other_weight=1, allow_empty=True):
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
        dept_score = other_weight * (filled_dept_req / total_dept_req)
    else:
        dept_score = other_weight

    for staffer in staffers:
        if staffer.antiroommates.intersection(staffers):
            raise AntiRequestException(f"{str(staffer)} anti-requested {', '.join([str(x) for x in staffer.antiroommates.intersection(staffers)])}")

    #print(f"Scores: {room_night_score} {roommate_score} {dept_score} {filled_dept_req} {total_dept_req} {', '.join([x.name for x in staffers])}")
    return room_night_score, roommate_score, dept_score

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
        for perm in itertools.permutations(roommates, n):
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
    all_matched = set.union(*rooms)
    return rooms

def combine_rooms(rooms):
    rooms = list(rooms)
    combined = []
    for room in rooms:
        if len(room) == 4:
            combined.append(room)
    for i in combined:
        rooms.remove(i)

    while rooms:
        best = None
        best_score = 0
        for perm in itertools.permutations(rooms, 2):
            try:
                if len(perm[0]) + len(perm[1]) > 4:
                    continue
                score = sum(score_room(set.union(*perm), allow_empty=False))
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
    return combined

def match_block(staffers):
    print(f"Starting with {len(staffers)} Staffers")
    matched = set()
    all_rooms = []
    for n in range(4, 1, -1):
        rooms = match_perfect(set(staffers), matched, n)
        all_rooms.extend(rooms)
        matched = matched.union(*rooms)
        print(f"Matched rooms of at least {n}")
        print(f"Got {len(rooms)} rooms and {len(matched)} total cumulative matches")
    
    remaining = set(staffers).difference(matched)
    print(f"Giving the remaining {len(remaining)} staffers their own rooms")
    all_rooms.extend([set([x]) for x in remaining])
    matched = set.union(*all_rooms)
    print(f"Now have {sum(map(len, all_rooms))} Staffers Matched of {len(staffers)} into {len(all_rooms)} rooms")
    assert len(matched) == len(staffers)

    start_len = len(all_rooms)
    all_rooms = combine_rooms(all_rooms)
    print(f"Combined {start_len} rooms into {len(all_rooms)}")

    all_rooms = combine_rooms(all_rooms)
    print(f"Combined {start_len} rooms into {len(all_rooms)}")
    return all_rooms

for block in hotel_blocks[:-1]:
    print(f"Matching {block['name']}")
    stats['block_counts'][block['name']] = 0
    block_staffers = []
    for staffer in staffers:
        if staffer.hotel_block == block['id']:
            block_staffers.append(staffer)
            stats['block_counts'][block['name']] += 1

    rooms = match_block(block_staffers)
    matched_staffers = set.union(*rooms)
    print(f"Matched {len(matched_staffers)} of {len(block_staffers)}")
    print(set(block_staffers).difference(matched_staffers))

print(json.dumps(stats, indent=2, sort_keys=True))
room_sizes = {4:0, 3:0, 2:0, 1:0, 0:0}
total_empty_slots = 0
total_empty_nights = {x: 0 for x in room_night_mapping.values()}
rooms = list(rooms)
rooms.sort(key=lambda x: sum(score_room(x, allow_empty=False)))
rooms.reverse()
for room in rooms:
    room_sizes[len(room)] += 1
    staffers = set(room)
    nights = set().union(*[x.room_nights for x in staffers])
    empty_nights = {x: 0 for x in nights}
    for staffer in staffers:
        for night in nights:
            if not night in staffer.room_nights:
                empty_nights[night] += 1
    for k, v in empty_nights.items():
        total_empty_nights[k] += v
    filled_slots = sum([len(x.room_nights) for x in staffers])
    total_slots = len(nights) * 4
    print(f"{filled_slots}, {total_slots}, {', '.join([str(x) for x in score_room(room, allow_empty=False)])}, {', '.join([str(x) for x in room])}")
    empty_slots = total_slots - filled_slots
    total_empty_slots += empty_slots

print(f"Total staffers roomed: {sum(map(len, rooms))}")
print(json.dumps(room_sizes, indent=2, sort_keys=True))
print(f"Total empty bed nights: {total_empty_slots}")
print(json.dumps(total_empty_nights, indent=2, sort_keys=True))