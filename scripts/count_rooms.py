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

BASE_URL = f'{TUBER_URL}/api/event/1'

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


assignments = get(f'{BASE_URL}/room_night_assignment')
room_nights = get(f'{BASE_URL}/hotel_room_night')
rooms = get(f'{BASE_URL}/hotel_room')

counts = {x['id']: {y['id']: 0 for y in room_nights} for x in rooms}

for a in assignments:
    counts[a['hotel_room']][a['room_night']] += 1

night_counts = {y['id']: 0 for y in room_nights}
total_empty = 0

for room, nights in counts.items():
    for night, total in nights.items():
        if total:
            night_counts[night] += 4 - total
            total_empty += 4 - total

print(f"Total empty bed nights: {total_empty}")
print(json.dumps(night_counts, indent=2, sort_keys=True))

#print(json.dumps(counts, indent=2, sort_keys=True))